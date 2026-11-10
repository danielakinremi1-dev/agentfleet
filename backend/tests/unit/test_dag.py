"""Dependency graphs: valid graphs are ordered, cyclic graphs are rejected with the cycle named."""

import itertools
import random

import pytest

from app.orchestration.dag import CycleError, topological_order

Graph = dict[str, list[str]]


def assert_valid_order(graph: Graph, order: list[str]) -> None:
    """The definition of a topological order: every task once, each after its dependencies."""
    assert sorted(order) == sorted(graph)
    position = {key: index for index, key in enumerate(order)}
    for key, depends_on in graph.items():
        for dependency in depends_on:
            assert position[dependency] < position[key], f"{key} came before {dependency}"


def assert_real_cycle(graph: Graph, cycle: list[str]) -> None:
    """A reported cycle must exist in the graph, not merely be a set of suspicious tasks."""
    assert len(cycle) >= 2
    assert cycle[0] == cycle[-1]
    assert len(set(cycle[:-1])) == len(cycle) - 1, "a task appears twice inside the cycle"
    for task, dependency in itertools.pairwise(cycle):
        assert dependency in graph[task], f"{task} does not depend on {dependency}"


# --- Acyclic graphs ----------------------------------------------------------


def test_empty_graph_has_an_empty_order() -> None:
    assert topological_order({}) == []


def test_single_task() -> None:
    assert topological_order({"a": []}) == ["a"]


def test_chain_is_ordered_even_when_defined_backwards() -> None:
    # Definition order must not be mistaken for execution order.
    graph = {"report": ["analyze"], "analyze": ["gather"], "gather": []}
    assert topological_order(graph) == ["gather", "analyze", "report"]


def test_diamond_runs_the_join_after_both_branches() -> None:
    graph: Graph = {
        "gather": [],
        "analyze_logs": ["gather"],
        "analyze_deploy": ["gather"],
        "compare": ["analyze_logs", "analyze_deploy"],
    }
    assert topological_order(graph) == ["gather", "analyze_logs", "analyze_deploy", "compare"]


def test_disconnected_tasks_keep_definition_order() -> None:
    # Independent tasks have no required order, so the result must still be predictable.
    graph: Graph = {"c": [], "a": [], "b": ["a"], "d": []}
    assert topological_order(graph) == ["c", "a", "d", "b"]


def test_result_is_deterministic() -> None:
    graph: Graph = {"x": [], "y": ["x"], "z": ["x"], "w": ["y", "z"]}
    assert all(topological_order(graph) == topological_order(graph) for _ in range(20))


def test_repeated_dependency_counts_as_one_edge() -> None:
    # Counting it twice would leave the task waiting forever and report a cycle that is not there.
    assert topological_order({"a": [], "b": ["a", "a"]}) == ["a", "b"]


def test_long_chain_does_not_exhaust_the_call_stack() -> None:
    # A recursive implementation fails here with RecursionError (the default limit is 1000).
    size = 5000
    graph = {f"t{i}": [f"t{i - 1}"] if i else [] for i in range(size)}
    assert topological_order(graph) == [f"t{i}" for i in range(size)]


# --- Cyclic graphs -----------------------------------------------------------


def test_two_task_cycle_is_reported() -> None:
    with pytest.raises(CycleError) as error:
        topological_order({"a": ["b"], "b": ["a"]})
    assert error.value.cycle == ["a", "b", "a"]
    assert "dependency cycle: a -> b -> a" in str(error.value)


def test_task_depending_on_itself_is_a_cycle() -> None:
    with pytest.raises(CycleError) as error:
        topological_order({"a": ["a"]})
    assert error.value.cycle == ["a", "a"]


def test_long_cycle_is_reported_in_full() -> None:
    graph = {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["e"], "e": ["a"]}
    with pytest.raises(CycleError) as error:
        topological_order(graph)
    assert error.value.cycle == ["a", "b", "c", "d", "e", "a"]


def test_tasks_downstream_of_a_cycle_are_not_reported_as_part_of_it() -> None:
    # "report" can never run, but it is a victim of the cycle, not a member. Naming it would
    # send the author of the template looking in the wrong place.
    graph: Graph = {"report": ["a"], "a": ["b"], "b": ["a"], "independent": []}
    with pytest.raises(CycleError) as error:
        topological_order(graph)
    assert error.value.cycle == ["a", "b", "a"]


def test_cycle_is_found_among_otherwise_valid_tasks() -> None:
    graph: Graph = {"start": [], "x": ["start", "z"], "y": ["x"], "z": ["y"], "end": ["start"]}
    with pytest.raises(CycleError) as error:
        topological_order(graph)
    assert_real_cycle(graph, error.value.cycle)
    assert set(error.value.cycle) == {"x", "y", "z"}


def test_unknown_dependency_is_an_error_not_a_cycle() -> None:
    with pytest.raises(ValueError, match="depends on unknown task 'missing'") as error:
        topological_order({"a": ["missing"]})
    assert not isinstance(error.value, CycleError)


# --- Randomized graphs -------------------------------------------------------
# Hand-picked cases cover the shapes someone thought of. Seeded random graphs check the
# definition itself on shapes nobody thought of, and stay reproducible because the seed is fixed.


def random_acyclic_graph(rng: random.Random, size: int) -> Graph:
    keys = [f"t{i}" for i in range(size)]
    # A task may only depend on tasks created before it, which rules out cycles by construction.
    graph = {key: [dep for dep in keys[:i] if rng.random() < 0.3] for i, key in enumerate(keys)}
    items = list(graph.items())
    rng.shuffle(items)  # So the input is not already in a valid order.
    return dict(items)


@pytest.mark.parametrize("seed", range(50))
def test_random_acyclic_graphs_are_ordered_correctly(seed: int) -> None:
    rng = random.Random(seed)
    graph = random_acyclic_graph(rng, rng.randint(1, 30))
    assert_valid_order(graph, topological_order(graph))


@pytest.mark.parametrize("seed", range(50))
def test_random_graphs_with_a_back_edge_report_a_real_cycle(seed: int) -> None:
    rng = random.Random(seed)
    graph = random_acyclic_graph(rng, rng.randint(2, 30))

    # Walk from a task to one of its ancestors, then make the ancestor depend on the task.
    start = rng.choice(list(graph))
    if not graph[start]:
        graph[start].append(next(key for key in graph if key != start))
    ancestor = start
    for _ in range(rng.randint(1, 5)):
        if not graph[ancestor]:
            break
        ancestor = rng.choice(graph[ancestor])
    graph[ancestor].append(start)

    with pytest.raises(CycleError) as error:
        topological_order(graph)
    assert_real_cycle(graph, error.value.cycle)
