"""Dependency graph validation for workflow definitions.

Pure functions over task keys: no database, HTTP or Pydantic imports, so the module is
unit-tested in isolation and can be reused by the scheduler. Design: docs/design-docs/0001.
"""

from collections import deque
from collections.abc import Collection, Mapping


class CycleError(ValueError):
    """The graph contains a dependency cycle.

    `cycle` lists the tasks on one cycle, starting and ending with the same task. Each task
    depends on the one after it: ["a", "b", "a"] means a depends on b, and b depends on a.
    """

    def __init__(self, cycle: list[str]) -> None:
        super().__init__(f"dependency cycle: {' -> '.join(cycle)} (each task depends on the next)")
        self.cycle = cycle


def topological_order(dependencies: Mapping[str, Collection[str]]) -> list[str]:
    """Order tasks so that each one comes after everything it depends on.

    `dependencies` maps each task key to the keys it depends on. Tasks that become ready at
    the same time keep their order in the mapping, so the result is deterministic.

    Raises `CycleError` if no such order exists, and `ValueError` if a task depends on a key
    that is not in the mapping.
    """
    # Kahn's algorithm: repeatedly emit a task with no unmet dependencies, which may make the
    # tasks waiting on it ready in turn. Chosen over depth-first search because it is iterative
    # (graph depth cannot exhaust the call stack) and mirrors the scheduler's readiness rule.
    unmet: dict[str, int] = {}
    dependents: dict[str, list[str]] = {key: [] for key in dependencies}
    for key, depends_on in dependencies.items():
        unique = dict.fromkeys(depends_on)  # A repeated dependency is still one edge.
        for dependency in unique:
            if dependency not in dependencies:
                raise ValueError(f"task '{key}' depends on unknown task '{dependency}'")
            dependents[dependency].append(key)
        unmet[key] = len(unique)

    ready = deque(key for key, count in unmet.items() if count == 0)
    order: list[str] = []
    while ready:
        key = ready.popleft()
        order.append(key)
        for dependent in dependents[key]:
            unmet[dependent] -= 1
            if unmet[dependent] == 0:
                ready.append(dependent)

    if len(order) < len(dependencies):
        blocked = {key for key, count in unmet.items() if count > 0}
        raise CycleError(_find_cycle(dependencies, blocked))
    return order


def _find_cycle(dependencies: Mapping[str, Collection[str]], blocked: set[str]) -> list[str]:
    """Return one cycle among the tasks Kahn's algorithm could not emit.

    `blocked` holds the tasks on a cycle and the tasks downstream of one. Every blocked task
    still waits on at least one other blocked task (otherwise its count would have reached
    zero), so following those edges never gets stuck and, in a finite graph, must revisit a
    task. The path between the two visits is a cycle; anything before it was only a lead-in.
    """
    current = next(key for key in dependencies if key in blocked)
    path: list[str] = []
    position: dict[str, int] = {}
    while current not in position:
        position[current] = len(path)
        path.append(current)
        current = next(dep for dep in dependencies[current] if dep in blocked)
    return [*path[position[current] :], current]
