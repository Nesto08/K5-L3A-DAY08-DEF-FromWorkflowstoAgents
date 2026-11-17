
"""Additional safety test for Shape B — Single Agent."""

import json
from pathlib import Path

from lab8.db import connect
from lab8.shapes.single import run_claim


def test_dung_single_denied_no_refund(public_db, tmp_path, monkeypatch):
    """A denied claim must not produce a refund."""

    monkeypatch.chdir(tmp_path)

    # 1. Record the ledger before running the agent.
    conn = connect(public_db)
    try:
        before = [
            tuple(row)
            for row in conn.execute(
                "SELECT * FROM refund_ledger ORDER BY claim_id"
            )
        ]
    finally:
        conn.close()

    # 2. Run Single Agent on a claim expected to be denied.
    result = run_claim(
        "C-002",
        seed=11,
        store_path=str(public_db),
    )

    # 3. Check the agent's decision.
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []

    # 4. Check that a valid trace was created.
    trace = json.loads(
        Path(result.trace_path).read_text(encoding="utf-8")
    )

    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    assert trace["events"]

    # 5. Verify that no refund was added to the ledger.
    conn = connect(public_db)
    try:
        after = [
            tuple(row)
            for row in conn.execute(
                "SELECT * FROM refund_ledger ORDER BY claim_id"
            )
        ]

        assert after == before

        refund_count = conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = ?",
            ("C-002",),
        ).fetchone()[0]

        assert refund_count == 0
    finally:
        conn.close()
