"""Structural TraceSight audit of pinned OpenRCA 2.0 telemetry.

Run after downloading normal/abnormal logs and traces under ROOT/cases.
No label, injection, causal graph, or manifest answer field is read by this script.
The manifest supplies only case names and system IDs, outside the feature path.
An exact identifier join is never treated as a verified execution witness.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REVISION = "581eba39d0bfd2d397eded6cd7cbe3303255521a"
KEY = ["trace_id", "span_id", "service_name"]
FILES = ("abnormal_logs", "abnormal_traces", "normal_logs", "normal_traces")


def valid_id(series):
    """Nonempty identifiers other than an all-zero sentinel (vectorised)."""
    text = series.fillna("").astype(str).str.strip()
    return text.ne("") & text.str.strip("0").ne("")


def valid_keys(table):
    return valid_id(table.trace_id) & valid_id(table.span_id) & valid_id(table.service_name)


def load(path, requested):
    schema = pq.read_schema(path).names
    columns = [column for column in requested if column in schema]
    table = pq.read_table(path, columns=columns).to_pandas()
    return table, set(schema)


def audit_window(folder, prefix):
    log_path = folder / f"{prefix}_logs.parquet"
    trace_path = folder / f"{prefix}_traces.parquet"
    result = {f"{prefix}_files_present": int(log_path.exists()) + int(trace_path.exists())}
    if not log_path.exists() or not trace_path.exists():
        return result
    logs, log_columns = load(log_path, KEY + ["message", "attr.log_template", "attr.template_id", "time"])
    spans, span_columns = load(trace_path, KEY + ["parent_span_id", "span_name", "attr.status_code", "attr.http.response.status_code", "time"])
    result.update({f"{prefix}_log_rows": len(logs), f"{prefix}_span_rows": len(spans)})
    result[f"{prefix}_log_columns"] = ";".join(sorted(log_columns))
    result[f"{prefix}_trace_columns"] = ";".join(sorted(span_columns))
    if not set(KEY).issubset(log_columns) or not set(KEY).issubset(span_columns):
        result[f"{prefix}_identity_schema_ok"] = False
        return result
    result[f"{prefix}_identity_schema_ok"] = True
    log_valid = valid_keys(logs)
    span_valid = valid_keys(spans)
    lk = pd.MultiIndex.from_frame(logs.loc[log_valid, KEY].astype(str))
    sk = pd.MultiIndex.from_frame(spans.loc[span_valid, KEY].astype(str))
    matched = lk.isin(sk.unique())
    result[f"{prefix}_valid_log_keys_rows"] = int(log_valid.sum())
    result[f"{prefix}_valid_span_keys_rows"] = int(span_valid.sum())
    result[f"{prefix}_exact_matched_log_rows"] = int(matched.sum())
    result[f"{prefix}_unique_exact_matched_keys"] = int(lk[matched].nunique())
    result[f"{prefix}_unique_trace_ids"] = int(spans.loc[span_valid, "trace_id"].nunique())
    result[f"{prefix}_span_key_duplicate_rows"] = int(len(sk) - sk.nunique())
    if "message" in logs:
        result[f"{prefix}_log_message_nonempty_rows"] = int(logs.message.fillna("").astype(str).str.strip().ne("").sum())
    if "attr.log_template" in logs:
        result[f"{prefix}_log_template_nonempty_rows"] = int(logs["attr.log_template"].fillna("").astype(str).str.strip().ne("").sum())
    if "parent_span_id" in spans:
        parent = valid_id(spans.parent_span_id)
        ids = pd.MultiIndex.from_frame(spans.loc[span_valid, ["trace_id", "span_id"]].astype(str))
        child = spans.loc[parent & valid_id(spans.trace_id), ["trace_id", "parent_span_id"]].astype(str)
        child.columns = ["trace_id", "span_id"]
        result[f"{prefix}_parent_link_rows"] = int(pd.MultiIndex.from_frame(child).isin(ids.unique()).sum())
        result[f"{prefix}_parent_id_rows"] = int(parent.sum())
    for column, field in [("attr.status_code", "span_status"), ("attr.http.response.status_code", "http_status")]:
        if column in spans:
            result[f"{prefix}_{field}_nonempty_rows"] = int(spans[column].fillna("").astype(str).str.strip().ne("").sum())
    if "attr.status_code" in spans:
        result[f"{prefix}_error_status_rows"] = int(spans["attr.status_code"].fillna("").astype(str).str.lower().eq("error").sum())
    if "attr.http.response.status_code" in spans:
        result[f"{prefix}_http_5xx_rows"] = int(pd.to_numeric(spans["attr.http.response.status_code"], errors="coerce").ge(500).sum())
    # No explicit retry/attempt identifier exists in the sampled standard schema.
    # Report per-case column presence rather than guessing attempts from span IDs.
    result[f"{prefix}_explicit_attempt_column"] = any("attempt" in c.lower() or "retry" in c.lower() for c in log_columns | span_columns)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("raw"))
    parser.add_argument("--manifest", type=Path, default=Path("manifest.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("audit_output"))
    parser.add_argument("--windows", nargs="+", choices=["abnormal", "normal"], default=["abnormal"])
    args = parser.parse_args()
    cases = [{k: obj[k] for k in ("name", "system")} for line in args.manifest.open() if (obj := json.loads(line))]
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, case in enumerate(cases, 1):
        folder = args.root / "cases" / case["name"]
        row = dict(case)
        for prefix in args.windows:
            try:
                row.update(audit_window(folder, prefix))
            except Exception as exc:
                row[f"{prefix}_audit_error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
        if i % 25 == 0:
            print(f"Audited {i}/{len(cases)} cases", flush=True)
    fields = sorted({key for row in rows for key in row})
    with (args.output / "cases.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {"revision": REVISION, "cases_in_manifest": len(cases), "systems": dict(Counter(r["system"] for r in rows)), "windows": args.windows, "scope": "Structural coverage only; no verified application-level witness semantics or root-cause accuracy."}
    for system in ["ALL", *sorted(summary["systems"])]:
        subset = [row for row in rows if system == "ALL" or row["system"] == system]
        group = {"cases": len(subset)}
        for prefix in args.windows:
            group[f"{prefix}_complete_files"] = sum(row.get(f"{prefix}_files_present") == 2 for row in subset)
            group[f"{prefix}_audit_errors"] = sum(bool(row.get(f"{prefix}_audit_error")) for row in subset)
            group[f"{prefix}_cases_with_exact_match"] = sum(row.get(f"{prefix}_exact_matched_log_rows", 0) > 0 for row in subset)
            group[f"{prefix}_cases_with_explicit_attempt_column"] = sum(bool(row.get(f"{prefix}_explicit_attempt_column")) for row in subset)
            for key in ("log_rows", "span_rows", "valid_log_keys_rows", "valid_span_keys_rows", "exact_matched_log_rows", "unique_exact_matched_keys", "span_key_duplicate_rows", "parent_id_rows", "parent_link_rows", "span_status_nonempty_rows", "http_status_nonempty_rows", "error_status_rows", "http_5xx_rows", "log_message_nonempty_rows", "log_template_nonempty_rows"):
                group[f"{prefix}_{key}"] = sum(int(row.get(f"{prefix}_{key}", 0)) for row in subset)
        summary[system] = group
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
