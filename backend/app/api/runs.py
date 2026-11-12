"""Workflow run endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import SessionDep
from app.schemas.run import RunCreate, RunDetailRead, RunRead, TaskRead
from app.services import workflow_runs
from app.services.workflow_runs import (
    InvalidTemplateDefinitionError,
    RunDetail,
    TemplateNotFoundError,
)

router = APIRouter(prefix="/api", tags=["runs"])


def _detail_response(detail: RunDetail) -> RunDetailRead:
    tasks = [
        TaskRead(
            id=task.id,
            key=task.key,
            name=task.name,
            status=task.status,
            depends_on=list(detail.depends_on[task.id]),
            attempt_count=task.attempt_count,
            output=task.output,
            error=task.error,
            started_at=task.started_at,
            finished_at=task.finished_at,
        )
        for task in detail.tasks
    ]
    return RunDetailRead(**RunRead.model_validate(detail.run).model_dump(), tasks=tasks)


@router.post(
    "/workflows/{template_id}/runs",
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Template not found"},
        409: {"description": "The template's stored definition is not a valid task graph"},
    },
)
async def create_run(
    template_id: uuid.UUID, body: RunCreate, session: SessionDep, response: Response
) -> RunDetailRead:
    """Create a run of a template. Every task starts `pending`; nothing is executed yet."""
    try:
        detail = await workflow_runs.create_run(session, template_id, body)
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "workflow template not found") from exc
    except InvalidTemplateDefinitionError as exc:
        # 409, not 422: the request is well-formed. It conflicts with the state of the template.
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    # The run is created under its template's path but lives at its own, so say where.
    response.headers["Location"] = f"/api/runs/{detail.run.id}"
    return _detail_response(detail)


@router.get("/runs")
async def list_runs(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RunRead]:
    """List runs, newest first, without their tasks."""
    runs = await workflow_runs.list_runs(session, limit=limit, offset=offset)
    return [RunRead.model_validate(run) for run in runs]


@router.get("/runs/{run_id}", responses={404: {"description": "Run not found"}})
async def get_run(run_id: uuid.UUID, session: SessionDep) -> RunDetailRead:
    """Return a run with its tasks and each task's dependencies."""
    detail = await workflow_runs.get_run(session, run_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "workflow run not found")
    return _detail_response(detail)
