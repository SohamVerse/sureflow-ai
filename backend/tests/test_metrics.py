"""Unit tests for evaluation/metrics.py — pure functions, no DB/network needed."""
import pytest

from evaluation.metrics import (
    compute_latency_ms,
    is_schema_valid,
    is_vetoed,
    requires_approval,
    compute_benchmark_aggregates,
    compute_campaign_summary,
)


class TestComputeLatencyMs:
    def test_converts_seconds_to_milliseconds(self):
        assert compute_latency_ms(start=0.0, end=1.5) == 1500

    def test_rounds_to_nearest_millisecond(self):
        assert compute_latency_ms(start=0.0, end=0.1234) == 123

    def test_never_returns_negative(self):
        # Defensive against a clock going backwards or args swapped.
        assert compute_latency_ms(start=5.0, end=1.0) == 0


class TestIsSchemaValid:
    def test_defaults_to_true_when_absent(self):
        assert is_schema_valid({}) is True

    def test_true_when_explicitly_set(self):
        assert is_schema_valid({"schema_valid": True}) is True

    def test_false_when_fallback_was_used(self):
        assert is_schema_valid({"schema_valid": False}) is False


class TestIsVetoed:
    def test_false_when_no_veto_decision(self):
        assert is_vetoed({}) is False

    def test_false_when_not_vetoed(self):
        assert is_vetoed({"veto_decision": {"vetoed": False}}) is False

    def test_true_when_vetoed(self):
        assert is_vetoed({"veto_decision": {"vetoed": True}}) is True


class TestRequiresApproval:
    def test_defaults_to_false(self):
        assert requires_approval({}) is False

    def test_true_when_flagged(self):
        assert requires_approval({"requires_human_approval": True}) is True


class TestComputeBenchmarkAggregates:
    def test_empty_input_returns_zero_sample_count_and_none_rates(self):
        result = compute_benchmark_aggregates([])
        assert result["sample_count"] == 0
        assert result["avg_confidence"] is None
        assert result["avg_latency_ms"] is None
        assert result["avg_cost"] is None
        assert result["schema_valid_rate"] is None
        assert result["veto_rate"] is None

    def test_averages_are_computed_correctly(self):
        evaluations = [
            {"confidence": 80.0, "latency_ms": 100, "cost": 0.01, "schema_valid": True, "vetoed": False},
            {"confidence": 60.0, "latency_ms": 200, "cost": 0.02, "schema_valid": True, "vetoed": False},
            {"confidence": 40.0, "latency_ms": 300, "cost": 0.0, "schema_valid": False, "vetoed": True},
        ]
        result = compute_benchmark_aggregates(evaluations)
        assert result["sample_count"] == 3
        assert result["avg_confidence"] == pytest.approx(60.0)
        assert result["avg_latency_ms"] == pytest.approx(200.0)
        assert result["avg_cost"] == pytest.approx(0.01)
        assert result["schema_valid_rate"] == pytest.approx(2 / 3)
        assert result["veto_rate"] == pytest.approx(1 / 3)

    def test_missing_confidence_and_latency_are_excluded_not_treated_as_zero(self):
        evaluations = [
            {"confidence": None, "latency_ms": None, "cost": 0.0, "schema_valid": True, "vetoed": False},
            {"confidence": 90.0, "latency_ms": 50, "cost": 0.0, "schema_valid": True, "vetoed": False},
        ]
        result = compute_benchmark_aggregates(evaluations)
        # Only the second row has real confidence/latency — the average
        # should reflect just that row, not be dragged toward zero.
        assert result["avg_confidence"] == pytest.approx(90.0)
        assert result["avg_latency_ms"] == pytest.approx(50.0)

    def test_all_schema_invalid_and_vetoed_gives_full_rates(self):
        evaluations = [
            {"confidence": 50.0, "latency_ms": 10, "cost": 0.0, "schema_valid": False, "vetoed": True},
        ]
        result = compute_benchmark_aggregates(evaluations)
        assert result["schema_valid_rate"] == pytest.approx(0.0)
        assert result["veto_rate"] == pytest.approx(1.0)


class TestComputeCampaignSummary:
    def test_empty_input_returns_zeroed_summary(self):
        result = compute_campaign_summary([])
        assert result["agent_count"] == 0
        assert result["agents_involved"] == []
        assert result["total_cost"] == 0.0
        assert result["total_latency_ms"] == 0
        assert result["had_schema_issues"] is False

    def test_sums_cost_and_latency_across_different_agents(self):
        evaluations = [
            {"agent_id": "CEO", "cost": 0.0, "latency_ms": 1000, "schema_valid": True},
            {"agent_id": "CMO", "cost": 0.0, "latency_ms": 2000, "schema_valid": True},
            {"agent_id": "RISK", "cost": 0.0117, "latency_ms": 4000, "schema_valid": True},
        ]
        result = compute_campaign_summary(evaluations)
        assert result["agent_count"] == 3
        assert result["agents_involved"] == ["CEO", "CMO", "RISK"]
        assert result["total_cost"] == pytest.approx(0.0117)
        assert result["total_latency_ms"] == 7000
        assert result["had_schema_issues"] is False

    def test_agents_involved_is_sorted_and_deduplicated(self):
        evaluations = [
            {"agent_id": "RISK", "cost": 0.0, "latency_ms": 1},
            {"agent_id": "CEO", "cost": 0.0, "latency_ms": 1},
            {"agent_id": "RISK", "cost": 0.0, "latency_ms": 1},
        ]
        result = compute_campaign_summary(evaluations)
        assert result["agents_involved"] == ["CEO", "RISK"]

    def test_had_schema_issues_true_if_any_row_failed_validation(self):
        evaluations = [
            {"agent_id": "CEO", "cost": 0.0, "latency_ms": 1, "schema_valid": True},
            {"agent_id": "SDR", "cost": 0.0, "latency_ms": 1, "schema_valid": False},
        ]
        result = compute_campaign_summary(evaluations)
        assert result["had_schema_issues"] is True
