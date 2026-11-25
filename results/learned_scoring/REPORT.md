# TraceSight real-data scorer pilot — 3 November 2026

This pilot uses cached OpenRCA 2.0 / ops-lite abnormal logs and spans. It is exploratory and **does not evaluate the complete TraceSight mechanism**.

## What ran

- Deterministic hash selection of 90 incident IDs without looking at labels.
- Service-level aggregate features from logs and spans; exact log–span key-match fraction.
- Incident-disjoint split: 62 train, 28 held out. Preprocessing and Logistic Regression fitted on training services only.
- Root labels read from the manifest solely to construct training targets and held-out metrics. Case IDs and service names are excluded from predictor columns. No injection record is read.
- Simple error-rate control on the same held-out incidents.

## Initial result

Among 28 held-out incidents, only 23 have a labelled root in the observed service candidate set; ranking metrics refer to these 23. Logistic Regression: Top-1 2/23 (8.7%), Top-3 10/23 (43.5%), MRR 0.309. Simple error-rate: Top-1 4/23 (17.4%), Top-3 8/23 (34.8%), MRR 0.334. The model does **not** demonstrate improvement.

The five root-absent cases must be reported separately; a ranker cannot retrieve a root omitted from its candidate set. This small, hash-selected sample and one split are insufficient for conclusions about generalisation. The benchmark release is designated for testing, so this exploratory training contaminates these 90 incidents for any future claim of untouched external evaluation. For final research, develop/train on separate suitable data and reserve genuinely untouched cases for external testing.

## Missing from a full TraceSight pilot

- No application-source-verified operation-start, success or retry witness rules.
- No justified request/attempt-level hidden execution variables built from real incidents.
- No compatible-history inference on real incident evidence, stable/ambiguous coverage, or missingness intervention.
- No normal-window baseline, metrics modality, cross-system test, statistical uncertainty or complete runtime profile.

An exact log–span join verifies recorded context, not operation outcome or why a record is missing. Do not transform it into a success/failure constraint. The existing synthetic inference engine remains a separate correctness reference until a semantic rule catalogue and case-to-history adapter are reviewed.

## Reproduce

From the repository root, with Python, pandas, pyarrow, numpy and scikit-learn installed:

```bash
python experiments/learned_scoring/real_data_pilot.py --root PATH_TO_CACHED_OPS_LITE_RAW --manifest PATH_TO_MANIFEST_JSONL --output local_runs/learned_scoring --max-cases 90
```

Raw telemetry is not included. `service_features.csv` contains target labels and must be kept outside the diagnostic input path; the script explicitly selects `FEATURES` for model fitting. `held_out_predictions.csv` is an evaluation artifact and also includes labels.

The case-level CSV files remain in the local historical archive, pending redistribution review.
