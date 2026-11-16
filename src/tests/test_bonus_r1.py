"""Validate the R1 investigator variant against labels and real crash recovery."""

import time

import pytest

from bonus.r1_investigator import run_claim
from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.metrics import trial_pass
from tests.conftest import BY_ID


@pytest.mark.parametrize("claim_id", ["C-002", "C-013", "C-014"])
def test_investigator_preserves_policy_and_order_caps(public_db, tmp_path, monkeypatch, claim_id):
    monkeypatch.chdir(tmp_path)
    started = time.time()
    result = run_claim(claim_id, seed=55, store_path=str(public_db))
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID[claim_id]["expected"], conn, started_at=started)
        assert passed, reason
    finally:
        conn.close()
    assert result.model_calls == 1


def test_investigator_crash_resume_remains_idempotent(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InjectedCrash):
        run_claim("C-012", seed=11, store_path=str(public_db), crash_at="after_effect_before_checkpoint")
    started = time.time()
    result = run_claim("C-012", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID["C-012"]["expected"], conn, started_at=started)
        assert passed, reason
    finally:
        conn.close()
