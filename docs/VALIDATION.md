# Consolidated repository verification — 26 November 2026

- 32 shared original files across the inference and LR snapshots were byte-identical. Core source, original tests and example fixtures preserved byte-for-byte.
- Python 3.13.5: `python -m pytest -q` — 23 passed, 1 adapter test module skipped (PyArrow unavailable). Historical report recorded 25 passing tests with the original dependencies.
- CLI fixtures: stable, ambiguous, conflict, computation_incomplete all reproduced.
- Controlled missingness: 15/15 checks passed in fresh execution; original → masked → restored produced 1 → 2 → 1 compatible states.
- Source compilation passed. Dataset experiments were not rerun; aggregate historical reports are retained. GitHub Actions is configured but has not been run remotely.
- Basic pattern screening found no obvious credential strings or old presentation-specific naming in the prepared text files; this is not a comprehensive security or licence audit.
