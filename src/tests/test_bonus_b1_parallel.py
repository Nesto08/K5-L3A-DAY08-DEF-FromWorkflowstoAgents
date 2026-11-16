from __future__ import annotations

from threading import Event

import pytest

from bonus.latency import flow_latency
from bonus.orchestrator_parallel import _run_read_tasks, run_claim as parallel_run
from lab8.app import prepare_store
from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.shapes.orchestrator import run_claim as serial_run


@pytest.mark.parametrize("claim_id", ["C-001", "C-002", "C-004", "C-005", "C-007", "C-013", "C-014"])
def test_parallel_orchestrator_matches_serial(tmp_path, claim_id):
    serial_store = tmp_path / f"serial-{claim_id}.sqlite"
    parallel_store = tmp_path / f"parallel-{claim_id}.sqlite"
    prepare_store(serial_store)
    prepare_store(parallel_store)

    serial = serial_run(claim_id, seed=55, store_path=str(serial_store))
    parallel = parallel_run(claim_id, seed=55, store_path=str(parallel_store))

    assert parallel.status == serial.status
    assert parallel.proposal_amount == serial.proposal_amount
    assert parallel.refund_effects == serial.refund_effects
    assert parallel.cost_estimate == serial.cost_estimate
    assert parallel.tool_calls == serial.tool_calls
    assert parallel.model_calls == serial.model_calls == 1

    conn = connect(parallel_store)
    serial_conn = connect(serial_store)
    try:
        assert get_refund(conn, claim_id) == get_refund(serial_conn, claim_id)
    finally:
        conn.close()
        serial_conn.close()


def test_parallel_reads_keep_declared_order_when_policy_finishes_first():
    order_started = Event()
    policy_finished = Event()

    def order_read():
        order_started.set()
        assert policy_finished.wait(timeout=3)
        return "order-result"

    def policy_read():
        assert order_started.wait(timeout=3)
        policy_finished.set()
        return "policy-result"

    results = _run_read_tasks(
        [("lookup_order", order_read), ("lookup_policy", policy_read)]
    )

    assert list(results) == ["lookup_order", "lookup_policy"]
    assert results == {
        "lookup_order": "order-result",
        "lookup_policy": "policy-result",
    }


def test_simulated_parallel_critical_path_is_seeded_and_shorter():
    serial = flow_latency(
        55,
        mode="serial",
        has_order=True,
        order_visible=True,
        refund_attempt=True,
    )
    parallel = flow_latency(
        55,
        mode="parallel",
        has_order=True,
        order_visible=True,
        refund_attempt=True,
    )
    repeated = flow_latency(
        55,
        mode="parallel",
        has_order=True,
        order_visible=True,
        refund_attempt=True,
    )

    assert parallel["critical_path_ms"] < serial["critical_path_ms"]
    assert repeated == parallel


def test_parallel_variant_resumes_crash_without_duplicate_refund(tmp_path):
    store = tmp_path / "parallel-crash.sqlite"
    prepare_store(store)

    with pytest.raises(InjectedCrash):
        parallel_run(
            "C-001",
            seed=11,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )
    result = parallel_run("C-001", seed=11, store_path=str(store))

    conn = connect(store)
    try:
        assert result.status == "resolved"
        assert get_refund(conn, "C-001")["amount_vnd"] == 35000
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()
