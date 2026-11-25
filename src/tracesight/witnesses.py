"""Scope-safe witness handling. Real log semantics require independent review."""

from dataclasses import dataclass
from .model import Constraint


@dataclass(frozen=True)
class Scope:
    incident: str
    service: str
    trace_id: str
    span_id: str
    operation: str
    attempt: str


@dataclass(frozen=True)
class Witness:
    scope: Scope
    event: str
    source: str
    semantic_reference: str
    verified: bool


def constraints_for(scope: Scope, variable_prefix: str,
                    witnesses: list[Witness]) -> list[Constraint]:
    """Compile only exact-scope, verified stage witnesses.

    Completion refers to the named operation, not service-wide health.
    Missing records and generic log emission deliberately add no hard rule.
    """
    mapping = {"handler_started": "entered", "operation_succeeded": "completed"}
    output = []
    for index, witness in enumerate(witnesses):
        if witness.scope != scope or not witness.verified or not witness.semantic_reference:
            continue
        if witness.event not in mapping:
            continue
        output.append(Constraint(
            f"witness_{index}_{witness.event}",
            (f"{variable_prefix}.{mapping[witness.event]}",), (("yes",),),
            (witness.source, witness.semantic_reference),
        ))
    return output
