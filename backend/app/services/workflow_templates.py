"""Workflow template use cases. Framework-agnostic: callable from the API, workers or scripts."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowTemplate
from app.schemas.workflow import WorkflowTemplateCreate


class TemplateNameConflictError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"a workflow template named '{name}' already exists")
        self.name = name


async def create_template(session: AsyncSession, data: WorkflowTemplateCreate) -> WorkflowTemplate:
    # ON CONFLICT DO NOTHING lets the unique constraint decide atomically, so two concurrent
    # requests with the same name cannot both succeed (no check-then-insert race), and a
    # conflict returns no row instead of aborting the transaction.
    statement = (
        insert(WorkflowTemplate)
        .values(
            name=data.name,
            description=data.description,
            definition=data.definition.model_dump(mode="json"),
        )
        .on_conflict_do_nothing(constraint="uq_workflow_templates_name")
        .returning(WorkflowTemplate)
    )
    template = await session.scalar(statement)
    if template is None:
        raise TemplateNameConflictError(data.name)
    # Commit before returning, so callers never report a write that is not yet durable.
    await session.commit()
    return template


async def get_template(session: AsyncSession, template_id: uuid.UUID) -> WorkflowTemplate | None:
    return await session.get(WorkflowTemplate, template_id)


async def list_templates(
    session: AsyncSession, *, limit: int, offset: int
) -> Sequence[WorkflowTemplate]:
    statement = (
        select(WorkflowTemplate)
        # id as a tie-breaker keeps pagination stable when timestamps are equal.
        .order_by(WorkflowTemplate.created_at.desc(), WorkflowTemplate.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await session.scalars(statement)).all()
