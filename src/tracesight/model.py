"""Typed, immutable input contract for the reference inference engine.

Variables describe execution facts, never root-cause labels. A term is a
declared contribution to a fixed scorer, not a probability or a causal proof.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Variable:
    name: str
    domain: tuple[str, ...]


@dataclass(frozen=True)
class Constraint:
    """Allowed joint assignments, with evidence/rule provenance."""

    name: str
    variables: tuple[str, ...]
    allowed: tuple[tuple[str, ...], ...]
    sources: tuple[str, ...]


@dataclass(frozen=True)
class Term:
    service: str
    when: tuple[tuple[str, str], ...]
    value: float
    sources: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    services: tuple[str, ...]
    variables: tuple[Variable, ...]
    constraints: tuple[Constraint, ...]
    base: dict[str, float]
    terms: tuple[Term, ...]
    sources: dict[str, str]
    scope: str

    def validate(self) -> None:
        """Reject malformed models instead of silently changing their meaning."""
        if not self.services or len(set(self.services)) != len(self.services):
            raise ValueError("Services must be nonempty and unique")
        domains = {v.name: v.domain for v in self.variables}
        if len(domains) != len(self.variables):
            raise ValueError("Variable names must be unique")
        for domain in domains.values():
            if not domain or len(set(domain)) != len(domain):
                raise ValueError("Domains must be nonempty and unique")
        if set(self.base) != set(self.services):
            raise ValueError("Base score keys must equal candidate services")
        for value in [*self.base.values(), *(t.value for t in self.terms)]:
            if not math.isfinite(value):
                raise ValueError("Scores must be finite")
        for constraint in self.constraints:
            if len(set(constraint.variables)) != len(constraint.variables):
                raise ValueError("Repeated variable in constraint")
            if any(v not in domains for v in constraint.variables):
                raise ValueError("Constraint references unknown variable")
            for row in constraint.allowed:
                if len(row) != len(constraint.variables):
                    raise ValueError("Wrong constraint row length")
                for name, value in zip(constraint.variables, row):
                    if value not in domains[name]:
                        raise ValueError("Constraint value outside domain")
        for term in self.terms:
            if term.service not in self.services:
                raise ValueError("Term references unknown service")
            if len(dict(term.when)) != len(term.when):
                raise ValueError("Repeated variable in score term")
            if any(n not in domains or v not in domains[n] for n, v in term.when):
                raise ValueError("Invalid score condition")
        for item in [*self.constraints, *self.terms]:
            if not item.sources or any(s not in self.sources for s in item.sources):
                raise ValueError("Every rule/term requires registered provenance")


def from_dict(data: dict) -> Problem:
    """Load only the declared inference schema; reject answer-key fields."""
    expected = {"services", "variables", "constraints", "base", "terms", "sources", "scope"}
    if set(data) != expected:
        raise ValueError(f"Unexpected/missing inference fields: {set(data) ^ expected}")
    problem = Problem(
        services=tuple(data["services"]),
        variables=tuple(Variable(v["name"], tuple(v["domain"])) for v in data["variables"]),
        constraints=tuple(Constraint(c["name"], tuple(c["variables"]),
                                    tuple(tuple(r) for r in c["allowed"]), tuple(c["sources"]))
                          for c in data["constraints"]),
        base={k: float(v) for k, v in data["base"].items()},
        terms=tuple(Term(t["service"], tuple(tuple(p) for p in t["when"]),
                         float(t["value"]), tuple(t["sources"])) for t in data["terms"]),
        sources=data["sources"], scope=data["scope"],
    )
    problem.validate()
    return problem
