"""Workflow coverage beyond the public student matrix."""

import json
from pathlib import Path

from lab8.db import connect
from lab8.shapes.workflow import run_claim


def test_unknown_claim_has_trace_without_changing_ledger(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    conn = connect(public_db)
    try:
        before = [tuple(row) for row in conn.execute("SELECT * FROM refund_ledger ORDER BY claim_id")]
    finally:
        conn.close()

    result = run_claim("C-UNKNOWN", seed=11, store_path=str(public_db))

    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    assert trace["events"]
    conn = connect(public_db)
    try:
        after = [tuple(row) for row in conn.execute("SELECT * FROM refund_ledger ORDER BY claim_id")]
        assert after == before
        assert conn.execute(
            "SELECT COUNT(*) FROM audit_events WHERE claim_id = ?", ("C-UNKNOWN",)
        ).fetchone()[0] == 0
    finally:
        conn.close()
