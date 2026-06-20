"""
Pure metric functions for the TrustedSkillRegistry (CompanyOS V3.1 Layer 6).

No DB access — cheap to unit test in isolation (see
backend/tests/test_skill_registry_metrics.py). ORM/DB concerns live in
skill_registry/registry.py.
"""
from __future__ import annotations


def compute_reputation(executions: list[dict]) -> dict:
    """
    Aggregate a list of execution-shaped dicts (success: bool, latency_ms: int)
    into reputation stats. trust_score is simply the success rate — a
    deliberately simple, honest definition rather than a more elaborate
    weighted formula that would just be dressing up the same signal.
    Returns None for empty input — there's no reputation to report yet.
    """
    n = len(executions)
    if n == 0:
        return {
            "total_calls": 0,
            "trust_score": None,
            "failure_rate": None,
            "avg_latency_ms": None,
        }

    successes = sum(1 for e in executions if e.get("success"))
    latencies = [e["latency_ms"] for e in executions if e.get("latency_ms") is not None]

    return {
        "total_calls": n,
        "trust_score": successes / n,
        "failure_rate": (n - successes) / n,
        "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
    }
