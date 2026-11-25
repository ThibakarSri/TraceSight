# Method contract

## Meaning of inputs

An inference model consists of candidate services, finite-domain execution
variables, allowed-tuple constraints, observed base scores, and additive
conditional score terms. Every constraint and term has registered source IDs.
The source registry must explain the observed base-score calculation too.
Domain choices and score terms are explicit modelling assumptions, not labels.

The initial exact witness scope includes incident, service, request/trace,
span, operation, and attempt. Attempt identity is mandatory for a verified
retry-sensitive rule. If unknown, do not fabricate an attempt identifier and
claim exact matching. The raw adapter only audits span-context association.

## Rules currently supported by the compiler

- Verified same-attempt handler-start witness constrains `entered=yes`.
- Verified same-operation success witness constrains `completed=yes`.
- Unverified evidence, generic log emission, and record absence impose no
  execution fact.
- Operation-success semantics do not establish overall business correctness
  or health of the whole service.

The caller supplies the actual semantic reference. A Boolean `verified` is a
review result, not an automated verification oracle. No real application log
template has been certified by this release. Its catalogue must be reviewed
against source instrumentation before use in scientific diagnosis claims.

Constraints such as `completed implies entered` must be explicitly encoded
for the modelled operation. Do not assume strict cross-machine timing without
clock/error assumptions. One request can contain retries and parallel work.

## Pairwise result

For each ordered service pair (i,j), compute the minimum of s_i-s_j over ALL
assignments satisfying ALL constraints. A strictly positive margin establishes
dominance within the declared model. Both nonpositive directions can mean a
tie or a reversal; inspect minimising states. Undominated candidates are not
necessarily jointly attainable winners and are not a probabilistic root set.

The reference algorithm costs O(product of domain sizes × constraint/scoring
cost), plus pairwise comparisons per feasible state. Enumeration is a reference,
not a scalable final algorithm. Budget truncation produces no certificate.

## Why joint constraints matter

The `joint_stable` fixture gives Payment=x+2 and Bank=x with shared x in {0,10}.
Independent ranges overlap: Payment [2,12], Bank [0,10]. Joint comparison is
always +2. This proves an implementation property on a tiny fixture, not a
new theorem or a measured benefit on microservice data.

## Novelty boundary

Constraints, conservative inference, exhaustive enumeration, linear scoring,
and pairwise dominance are established techniques. This version does not claim
algorithmic novelty. A research contribution requires useful request semantics,
a justified scorer, strong same-input baselines, and potentially a specific
ranking-preserving optimisation with evidence beyond this reference.

## Literature anchors

- Nezha (FSE 2023): https://github.com/IntelligentDDS/Nezha
- Groot (ASE 2021): https://taoxiease.github.io/publications/ase21-groot.pdf
- ARMOR manuscript: https://arxiv.org/html/2603.25538v3
- Partial-trace SFL: https://github.com/Bruno81930/SFL-Partial-Traces
- Conservative inference: https://people.idsia.ch/~zaffalon/papers/uai-2003.pdf

These motivate comparisons; none makes this implementation novel by association.
