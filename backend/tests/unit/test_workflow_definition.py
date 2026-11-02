"""Template definitions are validated before they reach the database."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas.workflow import MAX_TASKS_PER_TEMPLATE, WorkflowDefinition


def task(key: str, *depends_on: str) -> dict[str, Any]:
    return {"key": key, "name": key.replace("_", " ").title(), "depends_on": list(depends_on)}


def test_valid_dag_is_accepted() -> None:
    definition = WorkflowDefinition.model_validate(
        {
            "tasks": [
                task("gather_evidence"),
                task("analyze_logs", "gather_evidence"),
                task("analyze_deployment", "gather_evidence"),
                task("compare_findings", "analyze_logs", "analyze_deployment"),
            ]
        }
    )
    assert [t.key for t in definition.tasks][-1] == "compare_findings"


@pytest.mark.parametrize(
    ("tasks", "message"),
    [
        ([], "at least 1 item"),
        ([task("a"), task("a")], "duplicate task keys: a"),
        ([task("a", "missing")], "depends on unknown tasks: missing"),
        ([task("a", "a")], "depends on itself"),
        ([task("Bad-Key")], "should match pattern"),
        ([task(f"t{i}") for i in range(MAX_TASKS_PER_TEMPLATE + 1)], "at most 100 items"),
    ],
    ids=["empty", "duplicate-key", "unknown-dependency", "self-dependency", "bad-key", "too-many"],
)
def test_invalid_definitions_are_rejected(tasks: list[dict[str, Any]], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        WorkflowDefinition.model_validate({"tasks": tasks})


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WorkflowDefinition.model_validate({"tasks": [task("a")], "run_as_root": True})
