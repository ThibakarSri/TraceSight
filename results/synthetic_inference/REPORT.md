# Actual validation — 29 October 2026

25 tests passed in both the working environment and a fresh Python 3.12 virtual environment.
The installed CLI produced the expected stable fixture result. Dependency check passed.
All four statuses were exercised: stable, ambiguous, conflict, computation_incomplete.
No external deployment, Google Drive upload, or public repository publication occurred.

| System | Log rows | Span rows | Exact match / all logs | Exact duplicate rows | Conflicting keys |
|---|---:|---:|---:|---:|---:|
| tt | 7434 | 17443 | 94.32% | 0 | 0 |
| hs | 7085 | 5787 | 31.53% | 0 | 0 |
| otel | 1194 | 4526 | 67.34% | 1388 | 0 |

The real-data reports retained in the local historical archive are association audits, not execution-state diagnosis.
All return semantic_validation_required. No native collector-loss label is inferred.
The initial test discovery was mistakenly launched from the parent workspace,
which collected unrelated dependency tests; rerunning from the project root
succeeded. No failed inference test was hidden or converted into a passing result.

Fixture controls use synthetic scores. They do not establish improved RCA accuracy
or methodological novelty. Complete application semantics, real-data scoring,
strong baselines and full evaluation remain outstanding.
