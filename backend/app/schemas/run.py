import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import RunStatus, TaskStatus
from app.schemas.storable import contains_nul

# A run's input is context for its tasks, not a place to upload documents. The bound keeps one
# request from storing an arbitrarily large row (design doc 0001).
MAX_RUN_INPUT_BYTES = 64 * 1024


class RunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: dict[str, Any] = Field(default_factory=dict)

    @field_validator("input")
    @classmethod
    def check_input_can_be_stored(cls, value: dict[str, Any]) -> dict[str, Any]:
        if contains_nul(value):
            raise ValueError("input must not contain the NUL character (\\u0000)")
        try:
            # allow_nan=False makes NaN and Infinity an error. Python's JSON parser accepts
            # them, but they are not valid JSON and PostgreSQL's jsonb type rejects them.
            encoded = json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"))
        except ValueError:
            raise ValueError("input must not contain NaN or Infinity") from None
        size = len(encoded.encode())
        if size > MAX_RUN_INPUT_BYTES:
            raise ValueError(f"input is {size} bytes as JSON; the limit is {MAX_RUN_INPUT_BYTES}")
        return value


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_id: uuid.UUID
    status: RunStatus
    input: dict[str, Any]
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskRead(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    status: TaskStatus
    # Keys of the tasks that must complete before this one may start.
    depends_on: list[str]
    attempt_count: int
    output: dict[str, Any] | None
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None


class RunDetailRead(RunRead):
    """A run with its task graph. Tasks are listed in the order the template defined them."""

    tasks: list[TaskRead]
