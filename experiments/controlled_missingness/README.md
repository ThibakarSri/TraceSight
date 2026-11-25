# Controlled missingness experiment
A deterministic synthetic fixture tests whether removal of one verified completion event expands the compatible execution set without asserting failure. Run from the repository root with Python 3.11+:

```bash
python experiments/controlled_missingness/run_experiment.py
```
Outputs default to `local_runs/controlled_missingness/`; use `--output` to select another location. Saved reproducibility evidence lives in `results/controlled_missingness/`. The experiment imports the shared core and does not require a raw dataset or external Python packages. See `docs/WITNESS_RULE_CATALOGUE.csv` and `docs/WITNESS_AND_MISSINGNESS.md`. This is software correctness evidence, not real-world diagnostic accuracy.
