# TraceSight

**Root Cause Localisation in Microservices under Incomplete Telemetry Using Learned Scoring and Uncertainty-Preserving Ranking**

TraceSight investigates how comparing candidate services across compatible request executions affects diagnosis errors, decision coverage and computational cost. Missing observations are treated as unknown unless independently verified evidence establishes an execution fact. The project is an evolving research prototype, not a production RCA system.

## Method
1. Preserve evidence scope (incident, request, operation, attempt).
2. Compile verified observations into known facts; preserve unknown states.
3. Retain compatible execution histories under an explicit model.
4. Score candidates using observed base scores and history-dependent terms.
5. Compare rivals within the same history and across all compatible histories; report stable, ambiguous, conflict or computation incomplete.

A stable recommendation is conditional on the declared model, candidate set, constraints and scoring; it is not causal proof. The learned scorer is currently separate from the synthetic inference engine.

## Repository layout
| Path | Role |
|---|---|
| `src/tracesight/` | Reusable inference, models, witnesses, telemetry adapters, evaluation and CLI |
| `tests/` | Original automated correctness and data-adapter tests |
| `examples/` | Synthetic inference fixtures |
| `experiments/data_feasibility/` | Small association smoke test and 455-case structural audit |
| `experiments/learned_scoring/` | Exploratory real-data LR pilot |
| `experiments/controlled_missingness/` | Source-audited synthetic observation-removal experiment |
| `results/` | Historical aggregate measurements and synthetic validation outputs |
| `docs/` | Method contract, witness catalogue, roadmap, provenance and limitations |
| `.github/` | Automated checks and research-task templates |

## Quick start
Python 3.11+ (3.12 recommended for reproducibility).
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[data,dev]'
python -m pytest -q
tracesight infer examples/joint_stable.json --out local_runs/stable.json
python experiments/controlled_missingness/run_experiment.py
```
The synthetic engine and controlled missingness script require only the standard library. The optional data extra enables Parquet adapter tests; install `.[ml]` for the LR experiment. Historical dependency versions for the original reference run are in `requirements-tested.txt`. The exact original LR environment was not recovered. The example scores are illustrative, not calibrated probabilities. All new run outputs should go under `local_runs/` rather than overwrite historical measurements.

## Research evidence
| Experiment | Result | Interpretation |
|---|---|---|
| Three-case feasibility smoke test | 6 association checks passed; nominal first predictions missed all 3 roots | Preliminary data-handling evidence only |
| Full structural audit | 420/455 cases have an exact association; 6,701,436/7,912,995 valid-ID log rows match | Structural coverage, not verified execution witnesses |
| Synthetic inference | Four decision statuses; original report records 25 passing tests | Controlled correctness, not real-data accuracy |
| Learned scorer pilot | 90 incidents; 62 train / 28 held out; root present in 23; LR top-1 2/23 vs error-rate control 4/23 | Exploratory, does not demonstrate improvement |
| Controlled missingness | One completion event hidden: 1 → 2 → 1 compatible histories; stable → ambiguous → stable; 15 checks | Synthetic correctness under fixed illustrative scoring |

## Research status and next steps
Real application witness semantics, exact retry identity, candidate coverage, integrated learned scoring and a fair held-out comparative evaluation remain pending. See [roadmap](docs/RESEARCH_ROADMAP.md), [method contract](docs/METHOD_CONTRACT.md), [witness rules](docs/WITNESS_RULE_CATALOGUE.csv), [validation report](docs/WITNESS_AND_MISSINGNESS.md), and [data policy](docs/DATA_POLICY.md). The original standalone initial investigation is not recoverable from the available archives; no substitute result is asserted. The local source archives and historical detailed results are preserved separately.

## Publication and attribution
Use permitted data only. Raw telemetry, labels, case-level result tables and personal identifiers are excluded. The code and aggregate results should be reviewed for redistribution permissions. No open-source licence is granted implicitly. Supplemental research validation and repository preparation were AI-assisted; review and disclose as required. See [change history](docs/CHANGELOG.md).
