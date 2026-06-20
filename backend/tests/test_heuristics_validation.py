"""Unit tests for meta_learning/validation.py — pure functions, no DB/network needed."""
from meta_learning.validation import (
    validate_weights,
    format_heuristics_for_prompt,
    MIN_WEIGHT,
    MAX_WEIGHT,
)
from meta_learning.defaults import DEFAULT_HEURISTICS


class TestValidateWeights:
    def test_default_heuristics_are_valid(self):
        assert validate_weights(DEFAULT_HEURISTICS) == []

    def test_empty_dict_is_invalid(self):
        errors = validate_weights({})
        assert len(errors) == 1
        assert "non-empty" in errors[0]

    def test_value_below_min_is_invalid(self):
        errors = validate_weights({"urgency": MIN_WEIGHT - 0.1})
        assert len(errors) == 1
        assert "urgency" in errors[0]

    def test_value_above_max_is_invalid(self):
        errors = validate_weights({"urgency": MAX_WEIGHT + 0.1})
        assert len(errors) == 1
        assert "urgency" in errors[0]

    def test_boundary_values_are_valid(self):
        assert validate_weights({"a": MIN_WEIGHT, "b": MAX_WEIGHT}) == []

    def test_non_numeric_value_is_invalid(self):
        errors = validate_weights({"urgency": "high"})
        assert len(errors) == 1
        assert "must be a number" in errors[0]

    def test_boolean_value_is_invalid(self):
        # bool is technically an int subclass in Python — must be explicitly rejected.
        errors = validate_weights({"urgency": True})
        assert len(errors) == 1

    def test_multiple_errors_are_all_reported(self):
        errors = validate_weights({"a": -1.0, "b": "nope", "c": 5.0})
        assert len(errors) == 3


class TestFormatHeuristicsForPrompt:
    def test_empty_weights_returns_fallback_message(self):
        result = format_heuristics_for_prompt({})
        assert "No tuned heuristics" in result

    def test_known_tactic_includes_description(self):
        result = format_heuristics_for_prompt({"social_proof": 0.81})
        assert "social_proof = 0.81" in result
        assert "testimonials" in result

    def test_unknown_tactic_still_renders_with_generic_label(self):
        result = format_heuristics_for_prompt({"some_new_tactic": 1.2})
        assert "some_new_tactic = 1.2" in result
        assert "custom tactical weight" in result

    def test_output_is_wrapped_in_markers(self):
        result = format_heuristics_for_prompt(DEFAULT_HEURISTICS)
        assert result.startswith("=== TUNED HEURISTIC WEIGHTS")
        assert result.endswith("=== END HEURISTIC WEIGHTS ===")
