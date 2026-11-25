# Contributing

Use typed interfaces and small functions with explicit input/output contracts.
Document assumptions in docstrings, especially semantic and timing assumptions.
Keep dataset-specific logic in adapters and reviewed witness catalogues.
Do not add root labels to inference objects. Keep evaluator code separate.
Add meaningful correctness tests before changing constraints or ranking logic.
Keep generated telemetry, credentials and large datasets out of commits.
Run `python -m pytest -q` before a change is accepted.

Scientific claims must identify dataset revision, incident split, scorer
configuration, baseline implementation and measured uncertainty. Failed results
and excluded cases must be retained and explained. A nicer demonstration is
not evidence of higher accuracy. Synthetic tests must remain explicitly labelled.

Before public release: select an owner-approved code licence, check dataset
licences, verify author attribution, add a citation file with confirmed authors,
and complete a clean-environment reproduction run.
