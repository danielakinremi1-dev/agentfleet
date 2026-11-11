"""Turning a definition into rows is pure, so it is tested without a database."""

import uuid

from app.models import RunStatus, TaskStatus
from app.schemas.workflow import WorkflowDefinition
from app.services.workflow_runs import materialize

DIAMOND = WorkflowDefinition.model_validate(
    {
        "tasks": [
            {"key": "gather", "name": "Gather evidence"},
            {"key": "logs", "name": "Analyze logs", "depends_on": ["gather"]},
            {"key": "deploys", "name": "Check deployments", "depends_on": ["gather"]},
            {"key": "report", "name": "Write report", "depends_on": ["deploys", "logs"]},
        ]
    }
)


def test_one_pending_task_per_definition_entry_in_definition_order() -> None:
    template_id = uuid.uuid4()
    run, tasks, _ = materialize(template_id, DIAMOND, {"incident": "latency spike"})

    assert run.template_id == template_id
    assert run.status is RunStatus.PENDING
    assert run.input == {"incident": "latency spike"}
    assert [(task.position, task.key, task.name) for task in tasks] == [
        (0, "gather", "Gather evidence"),
        (1, "logs", "Analyze logs"),
        (2, "deploys", "Check deployments"),
        (3, "report", "Write report"),
    ]
    assert all(task.run_id == run.id and task.status is TaskStatus.PENDING for task in tasks)
    assert len({task.id for task in tasks}) == len(tasks)


def test_dependency_keys_become_task_ids_of_the_same_run() -> None:
    run, tasks, dependencies = materialize(uuid.uuid4(), DIAMOND, {})
    key_of = {task.id: task.key for task in tasks}

    assert all(edge.run_id == run.id for edge in dependencies)
    assert {(key_of[edge.task_id], key_of[edge.depends_on_task_id]) for edge in dependencies} == {
        ("logs", "gather"),
        ("deploys", "gather"),
        ("report", "deploys"),
        ("report", "logs"),
    }
    assert len(dependencies) == 4


def test_each_call_generates_new_ids() -> None:
    first_run, first_tasks, _ = materialize(uuid.uuid4(), DIAMOND, {})
    second_run, second_tasks, _ = materialize(uuid.uuid4(), DIAMOND, {})

    assert first_run.id != second_run.id
    assert {task.id for task in first_tasks}.isdisjoint(task.id for task in second_tasks)
