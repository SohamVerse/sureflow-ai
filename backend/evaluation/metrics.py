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


def compute_campaign_summary(evaluations: list[dict]) -> dict:
    """
    Summarize every Evaluation row sharing one run_id (CompanyOS V3.1 Layer 4
    — "cost per campaign"). Unlike compute_benchmark_aggregates (averages
    across many *separate* calls to the same agent/model), this sums across
    the *different* agents in one pipeline run.

    `had_schema_issues` reflects malformed-LLM-output fallbacks among calls
    that *did* produce an Evaluation row — it is not the same as a hard
    agent failure (an exception means no Evaluation row is ever created;
    those are tracked separately in AgentRunError, surfaced alongside this
    summary by api/routes.py::get_campaign rather than folded in here).
    """
    if not evaluations:
        return {
            "agent_count": 0,
            "agents_involved": [],
            "total_cost": 0.0,
            "total_latency_ms": 0,
            "had_schema_issues": False,
        }

    return {
        "agent_count": len(evaluations),
        "agents_involved": sorted({e["agent_id"] for e in evaluations if e.get("agent_id")}),
        "total_cost": sum(e.get("cost", 0.0) or 0.0 for e in evaluations),
        "total_latency_ms": sum(e.get("latency_ms", 0) or 0 for e in evaluations),
        "had_schema_issues": any(not e.get("schema_valid", True) for e in evaluations),
    }
