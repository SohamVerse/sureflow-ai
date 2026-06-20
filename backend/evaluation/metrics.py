"""
Pure metric functions for the EvaluatorBrain (CompanyOS V3.1 Layer 2).

Every function here is deterministic and takes plain dicts/values — no DB or
network access — so they're cheap to unit test in isolation (see
backend/tests/test_metrics.py). ORM/DB concerns live in evaluation/evaluator.py.
"""
from __future__ import annotations


def compute_latency_ms(start: float, end: float) -> int:
    """Convert a perf_counter() start/end pair (seconds) into whole milliseconds."""
    return max(0, round((end - start) * 1000))


def is_schema_valid(output: dict) -> bool:
    """Whether the agent's raw LLM output conformed to the BrainOutput contract
    without needing parse_brain_output's last-resort fallback (see core/brain.py)."""
    return bool(output.get("schema_valid", True))


def is_vetoed(output: dict) -> bool:
    """RISK-specific: whether this output carries an active veto decision.
    False (not vetoed) for every agent that doesn't produce a veto_decision."""
    return bool(output.get("veto_decision", {}).get("vetoed", False))


def requires_approval(output: dict) -> bool:
    """Whether this output was flagged for human review."""
    return bool(output.get("requires_human_approval", False))


def compute_benchmark_aggregates(evaluations: list[dict]) -> dict:
    """
    Aggregate a list of evaluation-shaped dicts (confidence, latency_ms, cost,
    schema_valid, vetoed) into benchmark summary stats. Returns zeroed-out
    rates (not None) for an empty input — callers decide whether an empty
    benchmark window is worth persisting.
    """
    n = len(evaluations)
    if n == 0:
        return {
            "sample_count": 0,
            "avg_confidence": None,
            "avg_latency_ms": None,
            "avg_cost": None,
            "schema_valid_rate": None,
            "veto_rate": None,
        }

    confidences = [e["confidence"] for e in evaluations if e.get("confidence") is not None]
    latencies = [e["latency_ms"] for e in evaluations if e.get("latency_ms") is not None]
    costs = [e.get("cost", 0.0) or 0.0 for e in evaluations]
    schema_valid_count = sum(1 for e in evaluations if e.get("schema_valid", True))
    veto_count = sum(1 for e in evaluations if e.get("vetoed", False))

    return {
        "sample_count": n,
        "avg_confidence": (sum(confidences) / len(confidences)) if confidences else None,
        "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
        "avg_cost": sum(costs) / n,
        "schema_valid_rate": schema_valid_count / n,
        "veto_rate": veto_count / n,
    }
