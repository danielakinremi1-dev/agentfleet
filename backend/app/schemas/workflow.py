import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# Task keys are referenced by `depends_on` and later by task rows, so keep them simple identifiers.
TaskKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$", max_length=100)]

MAX_TASKS_PER_TEMPLATE = 100


class TaskDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: TaskKey
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    depends_on: list[TaskKey] = Field(default_factory=list, max_length=MAX_TASKS_PER_TEMPLATE)


class WorkflowDefinition(BaseModel):
    """The task graph of a template.

    Validates structure only: unique keys and dependencies that point at known tasks.
    Cycle detection is added with the dependency graph module (Phase 1).
    """

    model_config = ConfigDict(extra="forbid")

    tasks: list[TaskDefinition] = Field(min_length=1, max_length=MAX_TASKS_PER_TEMPLATE)

    @model_validator(mode="after")
    def check_task_references(self) -> Self:
        keys = [task.key for task in self.tasks]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"duplicate task keys: {', '.join(duplicates)}")

        known = set(keys)
        for task in self.tasks:
            if task.key in task.depends_on:
                raise ValueError(f"task '{task.key}' depends on itself")
            unknown = sorted(set(task.depends_on) - known)
            if unknown:
                raise ValueError(
                    f"task '{task.key}' depends on unknown tasks: {', '.join(unknown)}"
                )
        return self


class WorkflowTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    description: Annotated[str, StringConstraints(max_length=2000)] = ""
    definition: WorkflowDefinition


class WorkflowTemplateRead(BaseModel):
    # from_attributes lets the response be built directly from the ORM object.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    definition: WorkflowDefinition
    created_at: datetime
    updated_at: datetime
