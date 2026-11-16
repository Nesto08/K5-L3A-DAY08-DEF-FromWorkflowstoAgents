"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        budget = Budget()
        trace = Trace(make_run_id("single", claim_id, seed))

        def finish_run(status: str, amount: int = 0, reason: str | None = None) -> RunResult:
            return finish(
                conn,
                shape="single",
                claim_id=claim_id,
                seed=seed,
                status=status,
                proposal_amount=amount,
                budget=budget,
                trace=trace,
                error_reason=reason,
            )

        # Chỉ đọc những cột cần thiết. Không đưa ticket/PII/secret vào trace.
        budget.add_tool(tool_cost())
        claim = conn.execute(
            "SELECT claim_id, principal_id, order_id FROM claims WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()

        if claim is None:
            trace.add("decision", {"status": "failed", "reason": "unknown_claim"})
            return finish_run("failed", reason="unknown_claim")

        if not claim["order_id"]:
            trace.add("decision", {"status": "needs_info"})
            return finish_run("needs_info", reason="missing_order_id")

        order_id = claim["order_id"]
        principal_id = claim["principal_id"]
        evidence: dict = {"order": None, "quote": None}

        # CP2: một Agent quyết định các công cụ chỉ đọc, tối đa 8 bước.
        def decide(observation: dict) -> dict:
            # Seeded MockLLM: tính model calls / tokens / cost vào Budget.
            # Prompt được giới hạn ở trạng thái công việc, không chứa raw ticket.
            last_tool = observation.get("last_tool")
            complete(
                budget,
                seed=seed,
                purpose="draft",
                prompt=f"single-agent next read step after {last_tool or 'start'}",
            )
            last_result = observation.get("last_result") or {}

            if last_tool is None:
                trace.add("tool_choice", {"tool": "lookup_order"})
                return {
                    "tool": "lookup_order",
                    "args": {"order_id": order_id, "principal_id": principal_id},
                }

            if last_tool == "lookup_order":
                if not last_result.get("visible"):
                    return {
                        "final": {
                            "status": "escalated",
                            "reason": last_result.get("reason") or "order_not_visible",
                        }
                    }
                evidence["order"] = dict(last_result["order"])
                trace.add("tool_choice", {"tool": "lookup_policy"})
                return {"tool": "lookup_policy", "args": {}}

            if last_tool == "lookup_policy":
                trace.add("tool_choice", {"tool": "lookup_refund_history"})
                return {
                    "tool": "lookup_refund_history",
                    "args": {"order_id": order_id, "principal_id": principal_id},
                }

            if last_tool == "lookup_refund_history":
                trace.add("tool_choice", {"tool": "compute_compensation"})
                return {
                    "tool": "compute_compensation",
                    "args": {"order": evidence["order"]},
                }

            if last_tool == "compute_compensation":
                evidence["quote"] = last_result
                return {"final": {"status": "quoted"}}

            return {"final": {"status": "failed", "reason": "unexpected_observation"}}

        react = run_react(
            conn,
            budget,
            observation={"claim": {"claim_id": claim_id}},
            decide=decide,
            max_steps=8,
            worker=False,
        )

        if react["stopped"] != "final":
            trace.add("decision", {"status": "failed", "reason": "step_cap"})
            return finish_run("failed", reason="step_cap")

        final = react["final"]
        if final.get("status") == "escalated":
            trace.add("decision", {"status": "escalated"})
            return finish_run("escalated", reason=final.get("reason"))

        if final.get("status") != "quoted":
            trace.add("decision", {"status": "failed"})
            return finish_run("failed", reason=final.get("reason") or "agent_failed")

        quote = evidence["quote"] or {}
        proposal = int(quote.get("amount_vnd", 0))
        trace.add("quote", {"amount_vnd": proposal})

        if proposal <= 0:
            trace.add("decision", {"status": "denied"})
            return finish_run("denied", reason=quote.get("reason"))

        # CP3: chỉ host ghi tiền. Chuyển FULL quote; không tự trừ lịch sử hoàn.
        try:
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise

        if not outcome["ok"]:
            status = "failed" if outcome["conflict"] else "denied"
            trace.add("decision", {"status": status})
            return finish_run(status, amount=proposal, reason=outcome["reason"])

        trace.add("decision", {"status": "resolved"})
        return finish_run("resolved", amount=proposal)
    finally:
        conn.close()
