# TraceSight: small dataset audit and mini PoC
Date: 28 October 2026

## Decision
Proceed with a larger dataset audit, NOT final dataset approval or a novelty claim.
Three previously cached published abnormal-telemetry incidents were processed, one per system. This is a convenience sample, not random or representative. No new production data was collected. Real telemetry was used; one matched span key per incident was hidden in memory as a controlled visibility test. This is an engineering smoke test; institutional permission for masking in the final evaluation remains unresolved.

## Actual audit results
|System|Log rows|Span rows|Exactly matched log rows|Match / all log rows|Unique matched span keys|Native unmatched valid log keys|Duplicate span keys|
|---|---:|---:|---:|---:|---:|---:|---:|
|TrainTicket|7434|17443|7012|94.32%|2677|11|0|
|Hotel Reservation|7085|5787|2234|31.53%|1315|2821|0|
|OTel Demo|1194|4526|804|67.34%|554|85|1388|

Exact matching uses the triple (trace_id, span_id, service_name), with blank/all-zero IDs excluded. Counts are log rows, not independent requests or incidents. Duplicate span keys mean repeated triples, not necessarily byte-identical rows. OTel duplicate/conflicting rows require an explicit resolution policy before substantive scoring. The tiny heuristic currently scores raw rows, so duplicates may bias it.

Unmatched logs are NOT classified as dropped telemetry. They may reflect window boundaries, instrumentation, scope mismatch, sampling, or other unknown causes. A matching log establishes an emission associated with that span context, subject to correct instrumentation; it does not automatically establish handler entry, entire-operation success, correct business outcome, or collector loss. Success-looking messages need operation-specific semantic review.

## Mini PoC actually implemented
1. Load published abnormal logs and spans.
2. Audit exact IDs and service-scoped associations.
3. Choose the lexicographically first matched key without reading root labels.
4. Remove all span rows with that key, preserving the corresponding log(s).
5. Verify that the witness remains available and that a different request ID is not treated as the selected witness.
6. Run three transparent scoring variants.
7. Read labels only afterwards for provenance and evaluation.

Six association checks passed (two per system). This validates small pieces of data handling, not inference correctness in general.

### Scoring variants: deliberately limited
Base score = fraction of observed spans with Error status or HTTP status >=500, per service.
- absence_penalty: base + 0.1 times number of log keys with no matching span.
- neutral_witness: base, no additional absence penalty.
- ambiguity_range: [base, base + 0.1 times unmatched keys]. Midpoint is used only for a displayed nominal ranking; a strict stable first exists only if its lower bound exceeds every other upper bound.

The 0.1 coefficient is illustrative, untrained and unjustified as fault evidence. It is NOT a proposed validated TraceSight scoring equation. These are three toy engineering controls, not ARMOR, Nezha, Groot, or a new algorithm. The range version has independent service intervals; it does not yet implement jointly constrained execution histories, request-state propagation, or pairwise optimisation over compatible worlds. Its missing penalty is intentionally a weak comparator. No superiority over strong baselines has been demonstrated.

## Outcomes and limitations
All nominal first predictions, including range midpoint rankings, missed the labelled root in these three cases. None had a stable range winner. This was an exploratory negative result, not a performance estimate. The full audit supersedes the small sample for corpus-level structural coverage, but this experiment uniquely documents early controlled span hiding and the inadequate toy missingness penalty.

## Reproduce
From the repository root, after installing the data extra:
```bash
mkdir -p local_runs/three_case
python experiments/data_feasibility/three_case/audit_poc.py --data-dir /path/to/cached/files --out local_runs/three_case/results.json
```
Expected local input names: `opslite_{tt,hs,otel}_abnormal_{logs,traces}.parquet` and `opslite_{tt,hs,otel}_label.json`. Labels are opened only after scoring. The exact case selections and hashes are preserved in the original private archive. Dataset: https://huggingface.co/datasets/anon-ops/ops-lite; cached metadata revision `581eba39d0bfd2d397eded6cd7cbe3303255521a`. The original cached bytes were not verified against the remote revision during that run. Only aggregate counts are published here; raw data, exact identifiers, label values and per-case predictions are not included. The historical experiment was not rerun during restructuring.
