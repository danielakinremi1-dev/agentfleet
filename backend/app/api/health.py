import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SessionDep

router = APIRouter(tags=["health"])

READINESS_TIMEOUT_SECONDS = 2.0


@router.get("/health")
async def liveness() -> dict[str, str]:
    """The process is up and serving requests. Does not touch dependencies."""
    return {"status": "ok"}


@router.get("/health/ready", responses={503: {"description": "Database unavailable"}})
async def readiness(session: SessionDep) -> dict[str, str]:
    """The service can do useful work: the database answers within a short timeout."""
    try:
        async with asyncio.timeout(READINESS_TIMEOUT_SECONDS):
            await session.execute(text("SELECT 1"))
    except (TimeoutError, OSError, SQLAlchemyError) as exc:
        # Deliberately generic: connection errors can contain hostnames or credentials.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database unavailable") from exc
    return {"status": "ready"}
