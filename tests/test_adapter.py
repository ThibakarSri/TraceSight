from pathlib import Path
import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("pyarrow")
from tracesight.adapters import audit


def test_native_data_gate_and_duplicate_policy(tmp_path):
    row = {"trace_id": "abc", "span_id": "def", "service_name": "Payment", "attr.status_code": "Error"}
    logs = tmp_path / "logs.parquet"
    traces = tmp_path / "traces.parquet"
    pd.DataFrame([row]).to_parquet(logs)
    pd.DataFrame([row, row, row | {"attr.status_code": "Unset"}]).to_parquet(traces)
    # Trap file deliberately invalid. Audit must not open adjacent answer keys.
    (tmp_path / "label.json").write_text("THIS MUST NOT BE READ")
    result = audit(logs, traces)
    assert result["matched_log_rows"] == 1
    assert result["exact_duplicate_span_rows"] == 1
    assert result["conflicting_span_keys"] == 1
    assert result["status"] == "semantic_validation_required"
    assert result["diagnostic_claim"] is False
    assert result["observed_error_rate_baseline"]["scores"] == {}


def test_zero_ids_do_not_match(tmp_path):
    row = {"trace_id": "000", "span_id": "000", "service_name": "Payment"}
    paths = [tmp_path / name for name in ("logs.parquet", "traces.parquet")]
    for path in paths:
        pd.DataFrame([row]).to_parquet(path)
    assert audit(*paths)["matched_log_rows"] == 0
