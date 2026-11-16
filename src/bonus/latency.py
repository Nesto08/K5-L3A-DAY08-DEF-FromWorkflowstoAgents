"""Deterministic latency estimates for the B1 critical-path model."""

from __future__ import annotations

import hashlib
from typing import Any

from lab8.config_loader import load_yaml


def operation_duration_ms(operation: str, seed: int, occurrence: int = 0) -> int:
    config = load_yaml("bonus/latency.yaml")
    try:
        base = int(config["operations"][operation]["base_ms"])
        jitter_range = int(config["jitter_range_ms"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid latency config for {operation}") from exc
    if base < 0 or jitter_range < 0:
        raise ValueError("latency and jitter values must be non-negative")
    digest = hashlib.sha256(f"{seed}|{operation}|{occurrence}".encode("utf-8")).digest()
    jitter = int.from_bytes(digest[:4], "big") % (2 * jitter_range + 1) - jitter_range
    return max(0, base + jitter)


def critical_path_ms(nodes: dict[str, dict[str, Any]]) -> int:
    """Return the longest dependency path for nodes listed in topological order."""
    finish_times: dict[str, int] = {}
    for name, node in nodes.items():
        dependencies = node.get("depends_on", [])
        missing = [dependency for dependency in dependencies if dependency not in finish_times]
        if missing:
            raise ValueError(f"{name} has missing or out-of-order dependencies: {missing}")
        start = max((finish_times[item] for item in dependencies), default=0)
        duration = int(node["duration_ms"])
        if duration < 0:
            raise ValueError(f"{name} duration must be non-negative")
        finish_times[name] = start + duration
    return max(finish_times.values(), default=0)


def flow_latency(seed: int, *, mode: str, has_order: bool, order_visible: bool, refund_attempt: bool) -> dict[str, Any]:
    """Build the same claim-flow DAG for serial and parallel investigator schedules."""
    if mode not in {"serial", "parallel"}:
        raise ValueError(f"unknown schedule mode: {mode}")

    nodes: dict[str, dict[str, Any]] = {
        "get_claim_view": {
            "duration_ms": operation_duration_ms("get_claim_view", seed),
            "depends_on": [],
        }
    }

    if has_order:
        nodes["lookup_order"] = {
            "duration_ms": operation_duration_ms("lookup_order", seed),
            "depends_on": ["get_claim_view"],
        }
        policy_dependencies = ["get_claim_view"]
        if mode == "serial":
            policy_dependencies = ["lookup_order"]
        nodes["lookup_policy"] = {
            "duration_ms": operation_duration_ms("lookup_policy", seed),
            "depends_on": policy_dependencies,
        }

        if order_visible:
            nodes["compute_compensation"] = {
                "duration_ms": operation_duration_ms("compute_compensation", seed),
                "depends_on": ["lookup_order", "lookup_policy"],
            }
            draft_dependencies = ["compute_compensation"]
        else:
            draft_dependencies = ["lookup_order", "lookup_policy"]

        nodes["model_draft"] = {
            "duration_ms": operation_duration_ms("model_draft", seed),
            "depends_on": draft_dependencies,
        }

        if order_visible and refund_attempt:
            nodes["issue_refund"] = {
                "duration_ms": operation_duration_ms("issue_refund", seed),
                "depends_on": ["model_draft"],
            }
    else:
        nodes["model_draft"] = {
            "duration_ms": operation_duration_ms("model_draft", seed),
            "depends_on": ["get_claim_view"],
        }

    return {
        "mode": mode,
        "nodes": nodes,
        "critical_path_ms": critical_path_ms(nodes),
    }
