# Research roadmap — development and evaluation

This is a planning document, not a claim of completed integration. The submitted proposal's question is: How does comparing services across compatible request executions affect diagnosis errors, decision coverage and computational cost?

| Work item | Current research evidence | Next acceptance criterion |
|---|---|---|
| Preserve scope | Three-case and 455-case structural audits | Validated incident/request/operation/attempt mapping, duplicate handling, eligibility counts |
| Witness semantics | Synthetic witness compiler; supplemental catalogue and upstream source review | Match raw records to exact deployed source/instrumentation versions; document conditions and unsupported states |
| Compatible histories | Exact synthetic PoC | Real verified evidence adapter; compare results to bounded exact reference |
| Learned scoring | 90-incident exploratory LR pilot; 2/23 root-present top-1 vs baseline 4/23 | Improve candidates and features on development groups; freeze preprocessing, scorer and rule weights |
| Ranking integration | Four synthetic statuses and controlled masking | Compare rivals within each compatible history; integration tests and resource caps |
| Final evaluation | Protocol planned | Group splits and untouched evaluation evidence; matched LR-only, fixed scorer + histories, one-history and simple event-rule controls; report firm-error with coverage, shortlist metrics, root ranks, runtime and RAM |

## Suggested GitHub issues (not yet created on GitHub)

1. Verify real event semantics and pinned deployment revisions.
2. Audit request and retry identity; determine eligible real cases.
3. Improve candidate generation and audit root-present coverage.
4. Develop source-linked real evidence adapter and integrate the history engine.
5. Validate and freeze learned scoring and history-rule weights.
6. Implement grouped evaluation and controlled missingness comparisons.
7. Profile exact inference and implement bounded computation safeguards.
8. Document results, negative findings, reproducibility and limitations.

Keep labels out of inference inputs. Do not infer a collector fault or successful execution from missing records. A stable ranking is conditional on the declared model, not causal proof.
