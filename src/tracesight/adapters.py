"""Read-only ops-lite telemetry audit, with no answer-key access.

Exact joins establish shared telemetry context, not handler entry, success,
collection loss, or retry identity. The adapter intentionally stops at the
semantic gate until application-specific witness rules are reviewed.
"""

from collections import Counter
from hashlib import sha256
from pathlib import Path


KEY_COLUMNS = ["trace_id", "span_id", "service_name"]


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_key(key: tuple[str, str, str]) -> bool:
    trace, span, service = key
    return bool(service and trace and span and set(trace) != {"0"} and set(span) != {"0"})


def audit(log_path: Path, trace_path: Path) -> dict:
    """Audit two explicitly supplied Parquet files. Never scan sibling files."""
    import pandas as pd  # Optional dependency: the inference core is stdlib-only.

    logs = pd.read_parquet(log_path)
    spans = pd.read_parquet(trace_path)
    for name, table in [("logs", logs), ("traces", spans)]:
        if any(column not in table for column in KEY_COLUMNS):
            raise ValueError(f"{name} lacks required identity columns")

    def keys(table):
        values = table[KEY_COLUMNS].fillna("").astype(str)
        return list(values.itertuples(index=False, name=None))

    log_keys, span_keys = keys(logs), keys(spans)
    available = {key for key in span_keys if valid_key(key)}
    first_span_row = {}
    for index, key in enumerate(span_keys):
        first_span_row.setdefault(key, index)
    examples = []
    for index, key in enumerate(log_keys):
        if valid_key(key) and key in available:
            examples.append((index, key))
        if len(examples) == 5:
            break
    valid_logs = [key for key in log_keys if valid_key(key)]
    matched = [key for key in valid_logs if key in available]
    repeated = len(span_keys) - len(set(span_keys))
    deduplicated = spans.drop_duplicates()
    unique_keys = keys(deduplicated)
    conflicting = {key for key, n in Counter(unique_keys).items() if n > 1 and valid_key(key)}
    # Baseline only: an observed symptom rate, not a causal diagnosis.
    clean = deduplicated.loc[[valid_key(k) and k not in conflicting for k in unique_keys]].copy()
    error = clean.get("attr.status_code", pd.Series("", index=clean.index)).fillna("").astype(str).str.lower().eq("error")
    http = pd.to_numeric(clean.get("attr.http.response.status_code", pd.Series(float("nan"), index=clean.index)), errors="coerce")
    rates = (error | http.ge(500)).groupby(clean.service_name).mean().to_dict()
    ordering = sorted(rates, key=lambda service: (-rates[service], service))
    return {
        "artifact_kind": "published_data_association_audit",
        "status": "semantic_validation_required",
        "log_rows": len(logs), "span_rows": len(spans),
        "valid_log_id_rows": len(valid_logs), "matched_log_rows": len(matched),
        "matched_log_percent": round(100 * len(matched) / len(logs), 2) if len(logs) else None,
        "unique_matched_keys": len(set(matched)),
        "unmatched_valid_log_keys": len(set(valid_logs) - available),
        "duplicate_span_key_rows": repeated,
        "exact_duplicate_span_rows": len(spans) - len(deduplicated),
        "conflicting_span_keys": len(conflicting),
        "observed_error_rate_baseline": {"scores": rates, "ranking": ordering},
        "diagnostic_claim": False,
        "interpretation": "A match establishes shared span context only; unmatched records do not prove collector loss.",
        "retry_identity_verified": False,
        "hashes": {"logs_sha256": file_hash(log_path), "traces_sha256": file_hash(trace_path)},
        "provenance": "Source row references use zero-based physical Parquet row order before cleaning.",
        "example_exact_matches": [
            {"trace_id": key[0], "span_id": key[1], "service": key[2],
             "log_source": f"logs.parquet#row={index}",
             "trace_source": f"traces.parquet#row={first_span_row[key]}",
             "conflicting_span_key": key in conflicting}
            for index, key in examples
        ],
    }
