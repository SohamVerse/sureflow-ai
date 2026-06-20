"""Unit tests for skill_registry/metrics.py — pure functions, no DB needed."""
import pytest

from skill_registry.metrics import compute_reputation


class TestComputeReputation:
    def test_empty_input_returns_none_stats(self):
        result = compute_reputation([])
        assert result["total_calls"] == 0
        assert result["trust_score"] is None
        assert result["failure_rate"] is None
        assert result["avg_latency_ms"] is None

    def test_all_successes_gives_perfect_trust_score(self):
        executions = [
            {"success": True, "latency_ms": 100},
            {"success": True, "latency_ms": 200},
        ]
        result = compute_reputation(executions)
        assert result["total_calls"] == 2
        assert result["trust_score"] == pytest.approx(1.0)
        assert result["failure_rate"] == pytest.approx(0.0)
        assert result["avg_latency_ms"] == pytest.approx(150.0)

    def test_all_failures_gives_zero_trust_score(self):
        executions = [{"success": False, "latency_ms": 50}] * 3
        result = compute_reputation(executions)
        assert result["trust_score"] == pytest.approx(0.0)
        assert result["failure_rate"] == pytest.approx(1.0)

    def test_mixed_results_compute_correct_rates(self):
        executions = [
            {"success": True, "latency_ms": 100},
            {"success": True, "latency_ms": 100},
            {"success": True, "latency_ms": 100},
            {"success": False, "latency_ms": 100},
        ]
        result = compute_reputation(executions)
        assert result["total_calls"] == 4
        assert result["trust_score"] == pytest.approx(0.75)
        assert result["failure_rate"] == pytest.approx(0.25)

    def test_missing_latency_values_are_excluded_from_average(self):
        executions = [
            {"success": True, "latency_ms": None},
            {"success": True, "latency_ms": 200},
        ]
        result = compute_reputation(executions)
        assert result["avg_latency_ms"] == pytest.approx(200.0)
