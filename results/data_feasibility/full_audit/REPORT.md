# TraceSight — OpenRCA 2.0 v2.1.0 data feasibility audit

**Dataset revision:** `581eba39d0bfd2d397eded6cd7cbe3303255521a` (`anon-ops/ops-lite`).  
**Scope:** All 455 published cases; every abnormal-window log and trace table. The repository inventory was checked for all ten Parquet telemetry tables per case.  
**Date:** 1 November 2026.  
**Question:** How many incidents are structurally eligible for request-linked evidence, and what remains to establish verified execution witnesses?

## Result

| System | Cases | Both abnormal files scanned | At least one exact log–span join | No exact join |
|---|---:|---:|---:|---:|
| TrainTicket | 275 | 275 | 267 | 8 |
| Hotel Reservation | 148 | 148 | 130 | 18 |
| OpenTelemetry Demo | 32 | 32 | 23 | 9 |
| **Total** | **455** | **455** | **420 (92.3%)** | **35 (7.7%)** |

Across all incidents there are 8,000,405 abnormal log rows and 17,786,360 abnormal span rows. Of 7,912,995 logs with nonempty, nonzero `(trace_id, span_id, service_name)`, 6,701,436 (84.7%) have an exact key in the same incident's trace table. This is a *row-weighted join rate*; it is not a percentage of incidents, proof of a completed operation, or RCA accuracy. The 420 cases are an **upper-bound candidate pool for request-linked witness review**, not 420 verified witness cases.

Of the 35 cases with no join, 27 have zero abnormal log rows, seven have logs but no valid full join key, and one has four valid log keys that do not match any span. All 455 have at least one abnormal span. The published repository has all ten expected telemetry Parquet filenames for each of the 455 cases. File presence alone does not establish nonempty or meaningful data.

## Additional coverage

| Structural observation | Total |
|---|---:|
| Valid span identity rows | 17,786,360 / 17,786,360 |
| Span rows with a nonzero parent ID | 16,970,667 |
| Parent IDs found within the same trace | 16,392,893 / 16,970,667 (96.6%) |
| Span rows with `attr.status_code = error` | 503,145 |
| Span rows with HTTP status >= 500 | 221,153 |
| Cases with at least one exact join and an error-status span somewhere in the incident | 376 |
| Cases with an explicit attempt/retry **column** in either table | 0 / 455 |

The error-status rows and exact joins have **not** been checked to refer to the same request or operation in this summary. The last row checks schema column names, not retry words inside messages or service-specific attributes. No collector-health or collector-status truth was established. Missing spans therefore cannot be assigned a verified cause from this audit.

## Method and interpretation

The script reads only `abnormal_logs.parquet` and `abnormal_traces.parquet` in each listed case. It discards blank and all-zero IDs, then matches exact `(trace_id, span_id, service_name)` triples *within that case*. Parent links match `(trace_id, parent_span_id)` to observed `(trace_id, span_id)`. A valid join establishes shared recorded span context. It does not establish handler entry, operation success, a retry number, collector failure, or why another record is missing.

The manifest is used solely for `name` and `system`. `root_services`, `label.json`, `injection.json`, `causal_graph.json`, and environment files are excluded from this audit and must not enter diagnosis features. The publisher says the ten telemetry Parquet tables alone are benchmark inference inputs.

**Semantic gate remains open.** We have not checked application source code and log templates across all systems to certify that specific messages prove `handler_started`, `operation_succeeded`, `timed_out`, or a particular attempt. Therefore the defensible number of *verified operation-level witness cases* is **not yet known**. It is incorrect to equate 420 with that number. Before claiming a working observation-aware diagnosis evaluation, define a small set of application-specific witness rules, validate them against source and sampled traces, count their matches by case, and then run the ranking method on held-out cases.

## Decision for TraceSight

The dataset **supports a substantial structural candidate pool** for request-linked log–trace analysis: 420 cases with at least one exact join. It does **not yet establish** that the current execution-history mechanism has verified witnesses or that retry identity and collector-loss hypotheses can be distinguished. Start with the 420 structurally eligible cases; report the stricter semantic subset after rule validation. The other 35 remain useful for service-level telemetry evaluation but cannot support an exact joined log–span witness in this abnormal window.

Normal-window rows, metrics content, controlled missingness experiments, root-label evaluation, and ML train/test splits were not audited here. This report is a dataset feasibility audit, not a root-cause performance result.

## Reproduce

Install `pandas`, `pyarrow`, and `huggingface_hub`. Download `manifest.jsonl` and all `cases/*/abnormal_logs.parquet` and `cases/*/abnormal_traces.parquet` at the pinned revision. Then run:

```bash
python audit_openrca.py --root raw --manifest manifest.jsonl --output audit_output
```

`cases.csv` gives every case's counts and schema, including the 35 without joins; `summary.json` contains totals. The source dataset is [anon-ops/ops-lite](https://huggingface.co/datasets/anon-ops/ops-lite) and its [dataset card](https://huggingface.co/datasets/anon-ops/ops-lite/blob/main/README.md) documents the benchmark input and answer-key boundary.
