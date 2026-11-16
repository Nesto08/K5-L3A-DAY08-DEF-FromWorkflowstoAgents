"""Build reproducible B1 serial-versus-parallel critical-path evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from bonus.latency import flow_latency
from lab8.compensation import quote
from lab8.console import utf8_stdio
from lab8.db import load_json, load_jsonl


def _percentile(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _flow_inputs(claim: dict[str, Any], world: dict[str, Any]) -> tuple[bool, bool, bool]:
    order_id = claim.get("order_id")
    if not order_id:
        return False, False, False
    order = next((row for row in world["orders"] if row["order_id"] == order_id), None)
    visible = order is not None and order["principal_id"] == claim["principal_id"]
    if not visible:
        return True, False, False
    entitlement = quote(order, world["policies"], as_of=str(world["as_of"]))
    return True, True, entitlement.amount_vnd > 0


def build_report(
    *,
    benchmark: dict[str, Any],
    world: dict[str, Any],
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    claim_by_id = {claim["claim_id"]: claim for claim in claims}
    trials = benchmark["trials"]
    samples: dict[str, list[int]] = {"serial": [], "parallel": []}
    details = []
    seen: set[tuple[str, int]] = set()

    for trial in trials:
        key = (trial["claim_id"], int(trial["seed"]))
        if key in seen:
            continue
        seen.add(key)
        claim = claim_by_id[trial["claim_id"]]
        has_order, order_visible, refund_attempt = _flow_inputs(claim, world)
        serial = flow_latency(
            trial["seed"],
            mode="serial",
            has_order=has_order,
            order_visible=order_visible,
            refund_attempt=refund_attempt,
        )
        parallel = flow_latency(
            trial["seed"],
            mode="parallel",
            has_order=has_order,
            order_visible=order_visible,
            refund_attempt=refund_attempt,
        )
        samples["serial"].append(serial["critical_path_ms"])
        samples["parallel"].append(parallel["critical_path_ms"])
        details.append(
            {
                "shape": trial["shape"],
                "claim_id": trial["claim_id"],
                "seed": trial["seed"],
                "serial_critical_path_ms": serial["critical_path_ms"],
                "parallel_critical_path_ms": parallel["critical_path_ms"],
            }
        )

    summaries = {}
    for mode, values in samples.items():
        summaries[mode] = {
            "trials": len(values),
            "critical_path_mean_ms": round(sum(values) / len(values), 3) if values else None,
            "critical_path_p95_ms": _percentile(values, 0.95),
        }

    serial_mean = summaries["serial"]["critical_path_mean_ms"]
    parallel_mean = summaries["parallel"]["critical_path_mean_ms"]
    speedup = round(serial_mean / parallel_mean, 4) if serial_mean and parallel_mean else None
    shape_stats = benchmark["by_shape"]
    compared_shapes = {}
    for shape in ("orchestrator", "orchestrator_parallel"):
        if shape in shape_stats:
            stats = shape_stats[shape]
            compared_shapes[shape] = {
                key: stats[key]
                for key in (
                    "trials",
                    "pass_rate",
                    "pass_5",
                    "seed_variance",
                    "cost_per_success_vnd",
                    "mean_steps",
                    "p95_steps",
                )
            }

    return {
        "source_benchmark": "reports/bonus_b1_benchmark.json",
        "latency_model": "bonus/latency.yaml",
        "latency_note": "Deterministic simulated latency; not measured wall-clock time.",
        "controlled_variables": benchmark["controlled_variables"],
        "critical_path": summaries,
        "mean_path_speedup": speedup,
        "shape_metrics": compared_shapes,
        "samples": details,
    }


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="Summarize B1 simulated critical paths")
    parser.add_argument("--benchmark", default="reports/bonus_b1_benchmark.json")
    parser.add_argument("--cases", default="data/public_claims.jsonl")
    parser.add_argument("--world", default="data/public_world_state.json")
    parser.add_argument("--out", default="reports/bonus_b1_latency.json")
    args = parser.parse_args(argv)

    benchmark = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    report = build_report(
        benchmark=benchmark,
        world=load_json(args.world),
        claims=load_jsonl(args.cases),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for mode, values in report["critical_path"].items():
        print(
            f"{mode}: mean={values['critical_path_mean_ms']} ms "
            f"p95={values['critical_path_p95_ms']} ms"
        )
    print(f"mean simulated path speedup: {report['mean_path_speedup']}x")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
