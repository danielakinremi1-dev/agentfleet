import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.orchestration.dag import topological_order
from app.schemas.storable import reject_nul

# Task keys are referenced by `depends_on` and later by task rows, so keep them simple identifiers.
TaskKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$", max_length=100)]

# Display names of templates and tasks.
Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    AfterValidator(reject_nul),
]

MAX_TASKS_PER_TEMPLATE = 100


class TaskDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: TaskKey
    name: Name
    depends_on: list[TaskKey] = Field(default_factory=list, max_length=MAX_TASKS_PER_TEMPLATE)


class WorkflowDefinition(BaseModel):
    """The task graph of a template.

    Valid when task keys are unique, every dependency names a known task exactly once, and
    the graph has no cycle, so at least one order exists in which the tasks can run.
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
            if len(set(task.depends_on)) != len(task.depends_on):
                raise ValueError(f"task '{task.key}' lists the same dependency more than once")
            unknown = sorted(set(task.depends_on) - known)
            if unknown:
                raise ValueError(
                    f"task '{task.key}' depends on unknown tasks: {', '.join(unknown)}"
                )

        # Raises CycleError, a ValueError, which Pydantic reports as a validation error (422).
        topological_order({task.key: task.depends_on for task in self.tasks})
        return self


class WorkflowTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    description: Annotated[str, StringConstraints(max_length=2000), AfterValidator(reject_nul)] = ""
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
