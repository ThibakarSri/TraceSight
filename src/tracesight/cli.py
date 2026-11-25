"""Reproducible CLI. Inference and audit commands do not accept root labels."""

import argparse
import json
import platform
from pathlib import Path
from time import perf_counter
import tracemalloc

from . import __version__
from .inference import infer
from .model import from_dict


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    solve = commands.add_parser("infer", help="Solve an explicit, provenance-backed state model")
    solve.add_argument("problem", type=Path)
    solve.add_argument("--max-assignments", type=int, default=100_000)
    solve.add_argument("--time-limit", type=float, default=10.0)
    audit_parser = commands.add_parser("audit", help="Audit published logs/traces; enforce semantic gate")
    audit_parser.add_argument("--logs", type=Path, required=True)
    audit_parser.add_argument("--traces", type=Path, required=True)
    for command in (solve, audit_parser):
        command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    start = perf_counter()
    tracemalloc.start()
    if args.command == "infer":
        data = json.loads(args.problem.read_text())
        result = infer(from_dict(data), args.max_assignments, args.time_limit)
    else:
        from .adapters import audit
        result = audit(args.logs, args.traces)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result["run"] = {
        "version": __version__, "python": platform.python_version(),
        "elapsed_seconds": perf_counter() - start,
        "peak_python_allocated_bytes": peak,
        "memory_note": "tracemalloc excludes some native-library allocations; not peak RSS",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"{result['status']}: {args.out}")


if __name__ == "__main__":
    main()
