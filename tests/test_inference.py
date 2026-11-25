"""Small executable correctness examples, not a research benchmark."""

from dataclasses import replace
import pytest

from tracesight.inference import infer
from tracesight.model import Constraint, Problem, Term, Variable, from_dict
from tracesight.witnesses import Scope, Witness, constraints_for
from tracesight.evaluation import ranking_metrics


@pytest.fixture
def coupled():
    # Shared uncertainty changes both scores together. Independent intervals
    # overlap, although Payment is always exactly two points above Bank.
    return Problem(
        ("Payment", "Bank"), (Variable("shared", ("low", "high")),), (),
        {"Payment": 2.0, "Bank": 0.0},
        (Term("Payment", (("shared", "high"),), 10.0, ("assumption",)),
         Term("Bank", (("shared", "high"),), 10.0, ("assumption",))),
        {"assumption": "Illustrative software-test score definition, not learned evidence"},
        "software_test_only",
    )


def test_joint_comparison_preserves_dependency(coupled):
    result = infer(coupled)
    assert result["stable_first"] == ["Payment"]
    assert result["comparisons"][0]["minimum_margin"] == 2
    assert result["baselines"]["independent_range_stable_first"] == []


def test_joint_constraint_excludes_impossible_combination(coupled):
    variables = (Variable("a", ("no", "yes")), Variable("b", ("no", "yes")))
    exclusive = Constraint("exclusive", ("a", "b"), (("no", "yes"), ("yes", "no")), ("assumption",))
    terms = (Term("Bank", (("a", "yes"), ("b", "yes")), 100, ("assumption",)),)
    result = infer(replace(coupled, variables=variables, constraints=(exclusive,), terms=terms))
    assert result["compatible_states"] == 2
    assert result["stable_first"] == ["Payment"]


def test_verified_witness_compiler_end_to_end(coupled):
    scope = Scope("case", "Payment", "r1", "s1", "pay", "A1")
    witness = Witness(scope, "operation_succeeded", "row7", "rule-v1", True)
    constraints = constraints_for(scope, "p", [witness])
    constraints.append(Constraint("stage_order", ("p.entered", "p.completed"),
                                  (("no", "no"), ("yes", "no"), ("yes", "yes")), ("rule-v1",)))
    problem = replace(coupled,
                      variables=tuple(Variable(n, ("no", "yes")) for n in ("p.entered", "p.completed")),
                      constraints=tuple(constraints), terms=(),
                      sources={"row7": "Synthetic same-operation success witness",
                               "rule-v1": "Software-test stage semantics; not a verified application rule"})
    result = infer(problem)
    assert result["compatible_states"] == 1
    assert result["comparisons"][0]["minimising_state"] == {"p.entered": "yes", "p.completed": "yes"}


def test_ambiguous(coupled):
    result = infer(replace(coupled, terms=(coupled.terms[1],)))
    assert result["status"] == "ambiguous"
    assert set(result["undominated_candidates"]) == {"Payment", "Bank"}


def test_conflicting_witnesses(coupled):
    constraints = tuple(Constraint(v, ("shared",), ((v,),), ("assumption",)) for v in ("low", "high"))
    result = infer(replace(coupled, constraints=constraints))
    assert result["status"] == "conflict"
    assert result["comparisons"] == []


def test_partial_search_never_certifies(coupled):
    result = infer(coupled, max_assignments=1)
    assert result["status"] == "computation_incomplete"
    assert result["stable_first"] == []


def test_exact_budget_is_complete(coupled):
    assert infer(coupled, max_assignments=2)["complete"]


def test_timeout_is_not_evidence_conflict(coupled):
    assert infer(coupled, time_limit=1e-12)["status"] == "computation_incomplete"


def test_ties_are_not_strict_dominance(coupled):
    result = infer(replace(coupled, base={"Payment": 0.0, "Bank": 0.0}))
    assert result["status"] == "ambiguous"


def test_no_variables_single_state(coupled):
    result = infer(replace(coupled, variables=(), terms=()))
    assert result["compatible_states"] == 1
    assert result["stable_first"] == ["Payment"]


def test_nan_rejected(coupled):
    with pytest.raises(ValueError):
        infer(replace(coupled, base={"Payment": float("nan"), "Bank": 0.0}))


def test_unknown_provenance_rejected(coupled):
    with pytest.raises(ValueError):
        infer(replace(coupled, sources={}))


def test_answer_key_rejected():
    with pytest.raises(ValueError):
        from_dict({"label": "Payment"})


@pytest.mark.parametrize("field,value", [("trace_id", "other"), ("attempt", "A2"),
                                         ("operation", "refund"), ("service", "Bank")])
def test_other_scope_never_matches(field, value):
    scope = Scope("case", "Payment", "r1", "s1", "pay", "A1")
    witness = Witness(replace(scope, **{field: value}), "operation_succeeded", "row", "rule", True)
    assert constraints_for(scope, "p", [witness]) == []


@pytest.mark.parametrize("verified,reference,event", [(False, "rule", "operation_succeeded"),
                                                     (True, "", "operation_succeeded"),
                                                     (True, "rule", "log_emitted"),
                                                     (True, "rule", "completion_span_missing")])
def test_unverified_or_absent_evidence_adds_no_fact(verified, reference, event):
    scope = Scope("case", "Payment", "r1", "s1", "pay", "A1")
    assert constraints_for(scope, "p", [Witness(scope, event, "row", reference, verified)]) == []


def test_verified_success_links_source():
    scope = Scope("case", "Payment", "r1", "s1", "pay", "A1")
    constraints = constraints_for(scope, "p", [Witness(scope, "operation_succeeded", "row7", "rule-v1", True)])
    assert constraints[0].variables == ("p.completed",)
    assert constraints[0].sources == ("row7", "rule-v1")


def test_multiple_required_roots_metrics():
    result = ranking_metrics(["Order", "Payment", "Bank"], {"Payment", "Bank"}, k=2)
    assert result["reciprocal_rank"] == 0.5
    assert result["required_recall_at_k"] == 0.5
