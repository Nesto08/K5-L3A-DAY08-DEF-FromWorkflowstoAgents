"""R1 ablation: add one read-only quote investigator before the same workflow.

The investigator uses structured data, has no write tool, and cannot override
the workflow. This measures redundant investigation overhead, not parallelism
or the capability of an independently reasoning production agent.
"""

from __future__ import annotations

import json
from pathlib import Path

from lab8.db import connect
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.workflow import run_claim as workflow
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str, *, seed: int, store_path: str, crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("workflow_investigator", claim_id, seed))
    conn = connect(store_path)
    try:
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        # Early invalid claims need no investigation. Never forward ticket text.
        if claim["found"] and claim["order_id"]:
            handoff = make_handoff(
                request_id=f"R1-{claim_id}", claim_id=claim_id,
                task="independently_check_structured_quote", facts={},
                allowed_tools=["lookup_order", "compute_compensation"],
            )
            trace.add("handoff", handoff)
            investigation = run_readonly_investigators(
                conn, budget, handoff, principal_id=claim["principal_id"],
            )
            tools = investigation["tools"]
            order_view = tools["lookup_order"]
            summary = {
                "visible": order_view["visible"],
                "reason": order_view["reason"],
                "quote": tools.get("compute_compensation"),
            }
            complete(budget, seed=seed, purpose="peer", prompt=json.dumps(summary, sort_keys=True))
            trace.add("investigator", summary)
    finally:
        conn.close()

    # Reuse the exact baseline decision and write path, including crash behavior.
    result = workflow(claim_id, seed=seed, store_path=store_path, crash_at=crash_at)
    original = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    for event in original["events"]:
        trace.add(event["kind"], event["payload"])
    result.shape = "workflow_investigator"
    result.run_id = trace.run_id
    result.trace_path = trace.write()
    result.model_calls += budget.model_calls
    result.tool_calls += budget.tool_calls
    result.input_tokens += budget.input_tokens
    result.output_tokens += budget.output_tokens
    result.cost_estimate = round(result.cost_estimate + budget.cost_estimate, 6)
    return result
