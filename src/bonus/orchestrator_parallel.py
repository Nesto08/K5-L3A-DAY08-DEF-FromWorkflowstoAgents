"""B1 variant: parallel read-only investigators with a single host-side writer."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from lab8.compensation import quote
from lab8.config_loader import as_of
from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, lookup_order, lookup_policy, tool_cost
from lab8.trace import Trace

_READ_ORDER = ("lookup_order", "lookup_policy")


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, store_path=store_path, crash_at=crash_at)
    finally:
        conn.close()


def _run_read_tasks(tasks: list[tuple[str, Callable[[], Any]]]) -> dict[str, Any]:
    """Run independent reads concurrently, but expose results in declaration order."""
    completed: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(tasks) or 1) as executor:
        futures = {executor.submit(task): name for name, task in tasks}
        for future in as_completed(futures):
            completed[futures[future]] = future.result()
    return {name: completed[name] for name, _ in tasks}


def _read_order(store_path: str, order_id: str, principal_id: str) -> dict[str, Any]:
    conn = connect(store_path)
    try:
        return lookup_order(conn, order_id, principal_id)
    finally:
        conn.close()


def _read_policy(store_path: str) -> dict[str, Any]:
    conn = connect(store_path)
    try:
        return lookup_policy(conn)
    finally:
        conn.close()


def _run(conn, claim_id: str, *, seed: int, store_path: str, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id("orchestrator_parallel", claim_id, seed)
    trace = Trace(run_id)

    claim = get_claim_view(conn, claim_id)
    trace.add("claim_view", safe_dump(claim))
    if not claim.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    if not claim.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt=f"needs_info:{claim_id}")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy"],
        max_output_tokens=400,
    )
    trace.add("handoff", safe_dump(handoff))

    # The investigator's claim-view read and two worker tool calls are costed
    # exactly as in the serial orchestrator.
    budget.add_tool(tool_cost())
    tasks = [
        (
            "lookup_order",
            lambda: _read_order(store_path, claim["order_id"], claim["principal_id"]),
        ),
        ("lookup_policy", lambda: _read_policy(store_path)),
    ]
    for _ in tasks:
        budget.add_tool(tool_cost())
    reads = _run_read_tasks(tasks)
    order_view = reads["lookup_order"]
    policy_view = reads["lookup_policy"]

    investigated: dict[str, Any] = {
        "claim_view": {
            key: claim[key]
            for key in ("found", "claim_id", "order_id")
            if key in claim
        },
        "tools": {
            "lookup_order": order_view,
            "lookup_policy": policy_view,
        },
    }

    quote_payload: dict[str, Any] | None = None
    if order_view.get("visible"):
        budget.add_tool(tool_cost())
        quote_result = quote(
            order_view["order"],
            policy_view["policies"],
            as_of=as_of(),
        )
        quote_payload = {
            "amount_vnd": quote_result.amount_vnd,
            "reason": quote_result.reason,
            "clause_ids": quote_result.clause_ids,
            "parts": quote_result.parts,
        }
        investigated["tools"]["compute_compensation"] = quote_payload

    trace.add("investigator", safe_dump(investigated))

    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt=f"escalated:{claim_id}")
        trace.add("decision", {"status": "escalated", "reason": order_view.get("reason")})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    proposal = int((quote_payload or {}).get("amount_vnd", 0))
    trace.add("quote", safe_dump(quote_payload or {}))
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        trace.add("decision", {"status": "denied", "reason": (quote_payload or {}).get("reason")})
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=(quote_payload or {}).get("reason"),
        )

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("issue_refund", safe_dump(outcome))
    if not outcome["ok"]:
        status = "failed" if outcome.get("conflict") else "denied"
        return finish(
            conn,
            shape="orchestrator_parallel",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome["reason"],
        )

    return finish(
        conn,
        shape="orchestrator_parallel",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
    )


