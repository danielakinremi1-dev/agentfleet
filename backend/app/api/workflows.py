"""Workflow template endpoints. Paths follow the roadmap: a "workflow" here is a template."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SessionDep
from app.schemas.workflow import WorkflowTemplateCreate, WorkflowTemplateRead
from app.services import workflow_templates
from app.services.workflow_templates import TemplateNameConflictError

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "A template with this name already exists"}},
)
async def create_workflow_template(
    body: WorkflowTemplateCreate, session: SessionDep
) -> WorkflowTemplateRead:
    try:
        template = await workflow_templates.create_template(session, body)
    except TemplateNameConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return WorkflowTemplateRead.model_validate(template)


@router.get("")
async def list_workflow_templates(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[WorkflowTemplateRead]:
    templates = await workflow_templates.list_templates(session, limit=limit, offset=offset)
    return [WorkflowTemplateRead.model_validate(t) for t in templates]


@router.get("/{template_id}", responses={404: {"description": "Template not found"}})
async def get_workflow_template(
    template_id: uuid.UUID, session: SessionDep
) -> WorkflowTemplateRead:
    template = await workflow_templates.get_template(session, template_id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "workflow template not found")
    return WorkflowTemplateRead.model_validate(template)
