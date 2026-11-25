# TraceSight — Witness-rule catalogue and controlled missingness experiment
**Supplemental validation | 26 November 2026 | Stage 2 → Stage 3 → Stage 5**

## Witness-rule catalogue
The historical PoC supports two positive witness events, `handler_started` and `operation_succeeded`. Its method contract says no real application log template had been certified. This extension verifies those rules for a small controlled emitter and documents candidate rules for future real-data use. Verification is conditional on authenticity, exact scope and source semantics; a Boolean `verified` is not a verification oracle.

| Rule | What is established | Status |
|---|---|---|
| WR-01 handler_started | Simulated payment handler reached its first observed step | Source-verified fixture; executable |
| WR-02 operation_succeeded | Defined simulated work succeeded | Source-verified fixture; executable |
| WR-03 matching trace/span/service | Shared recorded span context only | Specification + saved real association evidence |
| WR-04 explicit span status | Recorded status, interpreted according to instrumentation | Specification; dataset mapping pending |
| WR-05 missing/generic record | No additional execution fact | Conservative policy; tested |
| WR-06 Charge request received. | Handler reached upstream log site before charge call | Upstream source reviewed; dataset mapping pending |
| WR-07 Transaction complete. | Upstream log site reached after validation, before counter/return | Upstream source reviewed; dataset mapping pending |
| WR-08 demo.payment.charged | Baggage-dependent branch value in reviewed source | Upstream source reviewed; dataset mapping pending |

Full preconditions, exclusions and sources: `docs/WITNESS_RULE_CATALOGUE.csv`. Scope includes incident, service, trace, span, operation and attempt; do not invent retry identity. The local fixture records actual emission at the source sites in `experiments/controlled_missingness/fixture.py` (entry at line 17, success at 22). Both are compiled by the original engine. Its `completed` variable is defined here as successful simulated work, not client receipt or financial settlement.

### Saved real-data association evidence
The historical OpenTelemetry Demo association audit contains exact matching identifiers and source row references. These records remain in the local original archive pending redistribution review. Matching context alone does not establish successful execution; the raw log body and exact deployed source revision still require review.

### Source-review finding
The reviewed upstream Payment handler emits `Charge request received.` before awaiting the charge operation. The charge function emits `Transaction complete.` after its shown validation logic, before incrementing the counter and returning a transaction ID. The `demo.payment.charged` attribute follows a baggage branch. These are different witnesses; none independently proves actual settlement, response delivery or root cause. Since the inspected upstream main snapshot is not proven to match the dataset deployment, no real execution constraint is enabled from these observations.

## Controlled missingness
Question: does removing a verified completion observation preserve uncertainty rather than assign failure? One deterministic synthetic execution produces E1 (entry) and E2 (successful simulated work). The intervention removes only E2; then restores it. Same candidate set, domains, execution constraints, fixed scores and engine across all variants. The scorer is deliberately illustrative: Checkout=6; Payment=2 plus 7 if entered=yes and completed=no. No ground-truth root is assigned. `completed=no` in a history means the modeled successful work did not occur, not proof of a specific terminal failure.

| Variant | Entry | Completion | Histories | Decision | Minimum Checkout−Payment margin |
|---|---|---|---:|---|---:|
| Original | Yes | Yes | 1 | Stable: Checkout | 4 |
| Masked | Yes | Unknown | 2 | Ambiguous: Checkout / Payment | -3 |
| Restored | Yes | Yes | 1 | Stable: Checkout | 4 |

In masked history H1 (entered=yes, completed=no), Checkout=6, Payment=9. In H2 (entered=yes, completed=yes), Checkout=6, Payment=2. The minimum Payment−Checkout margin is -4, so neither candidate strictly dominates. The last verified progress moves back from successful work to entry. Restoration reproduces the logical result. A stable result is conditional on the model, not a verified fault.

**Actual run:** 15/15 checks passed, including retained entry, unknown completion, expansion of histories, stable/ambiguous/restored outcomes, same scorer, no masked source leakage, wrong retry rejection, unreviewed emitter rejection, absent attempt rejection and no success emission on the unsuccessful path. See `results/controlled_missingness/run_log.txt` and `results/controlled_missingness/results/checks.json`. These are new supplemental checks, not an addition to the original 25 historical pytest tests. Do not add the counts together as a single test-suite result.

**Reproduction:** run `python experiments/controlled_missingness/run_experiment.py` from the repository root. The original engine is imported unchanged; no third-party packages required. The ground-truth manifest is evaluator-only and never read by inference. The report is a single synthetic correctness demonstration, not a statistically representative experiment, collector-loss test, learned scoring evaluation or evidence of improved RCA accuracy.

## Remaining real-data milestone
Retrieve exact pinned raw Parquet records, identify source revision and instrumentation/library version, validate field mappings and emission sites, audit supported request/attempt identities and negative cases, then freeze approved witness rules before integrating the learned scorer and performing grouped real-data evaluation. Rules without verified conditions must remain disabled. Existing real-data pilot performance is unchanged.

## Sources reviewed (26 November 2026)
- Original TraceSight v0.1.0: `docs/METHOD_CONTRACT.md`, `src/tracesight/witnesses.py`, `src/tracesight/inference.py`, the original local association report, `tests/test_inference.py`.
- OpenTelemetry Logs Data Model, Trace Context Fields: https://opentelemetry.io/docs/specs/otel/logs/data-model/#trace-context-fields
- OpenTelemetry Trace API, Set Status: https://opentelemetry.io/docs/specs/otel/trace/api/#set-status
- OpenTelemetry HTTP span semantic conventions: https://opentelemetry.io/docs/specs/semconv/http/http-spans/
- OpenTelemetry Demo Payment Service: https://opentelemetry.io/docs/demo/services/payment/
- Upstream application source (reviewed main snapshot; deployment revision unverified): https://github.com/open-telemetry/opentelemetry-demo/blob/main/src/payment/index.js and https://github.com/open-telemetry/opentelemetry-demo/blob/main/src/payment/charge.js

New AI-assisted supplemental work; review, reproduce and disclose according to module requirements before using the work in assessed research. The original historical archive is unchanged. During repository consolidation the fixture version label and output paths were updated and the experiment rerun; the inference logic and fixed scoring definition are unchanged.
