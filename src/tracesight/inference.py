"""Exact bounded enumeration: a correctness reference, not a novel optimiser."""

from itertools import product
import math
from time import perf_counter

from .model import Problem


def score(problem: Problem, state: dict[str, str]) -> dict[str, float]:
    scores = dict(problem.base)
    for term in problem.terms:
        if all(state[name] == value for name, value in term.when):
            scores[term.service] += term.value
    return scores


def infer(problem: Problem, max_assignments: int = 100_000,
          time_limit: float = 10.0, tolerance: float = 1e-9) -> dict:
    """Evaluate all assignments, or explicitly return computation_incomplete.

    No stable ranking is emitted from a partial search. Conflict is asserted
    only after exhaustive search finds no compatible state. Constraints are
    evaluated jointly, so shared evidence cannot be independently reused.
    """
    problem.validate()
    if max_assignments < 1 or not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("Positive finite search budgets required")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Tolerance must be finite and nonnegative")
    start = perf_counter()
    pairs = [(i, j) for i in problem.services for j in problem.services if i != j]
    margins = {p: math.inf for p in pairs}
    witnesses = {}
    bounds = {s: [math.inf, -math.inf] for s in problem.services}
    first = None
    examined = compatible = 0
    complete = True
    names = [v.name for v in problem.variables]
    for values in product(*(v.domain for v in problem.variables)):
        if examined >= max_assignments or perf_counter() - start >= time_limit:
            complete = False
            break
        examined += 1
        state = dict(zip(names, values))
        if not all(tuple(state[v] for v in c.variables) in c.allowed for c in problem.constraints):
            continue
        compatible += 1
        scores = score(problem, state)
        if first is None:
            first = scores
        for s, value in scores.items():
            bounds[s] = [min(bounds[s][0], value), max(bounds[s][1], value)]
        for pair in pairs:
            difference = scores[pair[0]] - scores[pair[1]]
            if difference < margins[pair]:
                margins[pair] = difference
                witnesses[pair] = state.copy()
    result = {
        "scope": problem.scope, "examined_assignments": examined,
        "compatible_states": compatible, "complete": complete,
        "seconds": perf_counter() - start, "sources": problem.sources,
        "constraint_sources": {c.name: list(c.sources) for c in problem.constraints},
        "score_definition": {"base": problem.base,
                             "terms": [{"service": t.service, "when": list(t.when),
                                        "value": t.value, "sources": list(t.sources)}
                                       for t in problem.terms]},
        "guarantee": "Relative to supplied constraints and scorer only; not root correctness",
    }
    if not complete:
        return result | {"status": "computation_incomplete", "stable_first": [], "comparisons": []}
    if not compatible:
        return result | {"status": "conflict", "stable_first": [], "comparisons": []}
    stable = [i for i in problem.services
              if all(i == j or margins[i, j] > tolerance for j in problem.services)]
    undominated = [j for j in problem.services
                   if not any(i != j and margins[i, j] > tolerance for i in problem.services)]
    comparisons = [{"left": i, "right": j, "minimum_margin": margins[i, j],
                    "always_above": margins[i, j] > tolerance,
                    "minimising_state": witnesses[i, j]} for i, j in pairs]
    # A deterministic first feasible assignment is a control, NOT MAP inference.
    first_order = sorted(problem.services, key=lambda s: (-first[s], s))
    base_order = sorted(problem.services, key=lambda s: (-problem.base[s], s))
    independent = [i for i in problem.services
                   if all(i == j or bounds[i][0] - bounds[j][1] > tolerance for j in problem.services)]
    return result | {
        "status": "stable" if stable else "ambiguous", "stable_first": stable,
        "undominated_candidates": undominated, "comparisons": comparisons,
        "score_ranges": bounds,
        "baselines": {"observed_only": base_order, "first_feasible_state": first_order,
                      "independent_range_stable_first": independent},
        "tie_policy": "Baseline lists use service-name tie breaks; ties are not strict dominance",
    }
