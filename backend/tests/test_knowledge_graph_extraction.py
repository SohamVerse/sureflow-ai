"""Unit tests for knowledge_graph/extraction.py — pure functions, no Neo4j needed."""
from knowledge_graph.extraction import extract_competitors, extract_trends


class TestExtractCompetitors:
    def test_empty_research_output_returns_empty_list(self):
        assert extract_competitors({}) == []

    def test_extracts_well_formed_entries(self):
        research_output = {
            "competitor_intelligence": [
                {"competitor": "Acme Co", "recent_moves": "Raised Series B",
                 "weakness": "Slow support", "threat_level": "high"},
            ]
        }
        result = extract_competitors(research_output)
        assert result == [{
            "name": "Acme Co",
            "recent_moves": "Raised Series B",
            "weakness": "Slow support",
            "threat_level": "high",
        }]

    def test_skips_entries_with_no_name(self):
        research_output = {
            "competitor_intelligence": [
                {"recent_moves": "no name here", "threat_level": "high"},
                {"competitor": "", "threat_level": "high"},
            ]
        }
        assert extract_competitors(research_output) == []

    def test_skips_non_dict_entries(self):
        research_output = {"competitor_intelligence": ["just a string", 42, None]}
        assert extract_competitors(research_output) == []

    def test_invalid_threat_level_defaults_to_medium(self):
        research_output = {
            "competitor_intelligence": [{"competitor": "Acme", "threat_level": "catastrophic"}]
        }
        result = extract_competitors(research_output)
        assert result[0]["threat_level"] == "medium"

    def test_non_list_competitor_intelligence_returns_empty(self):
        assert extract_competitors({"competitor_intelligence": "not a list"}) == []

    def test_missing_optional_fields_default_to_empty_string(self):
        research_output = {"competitor_intelligence": [{"competitor": "Acme"}]}
        result = extract_competitors(research_output)
        assert result[0]["recent_moves"] == ""
        assert result[0]["weakness"] == ""
        assert result[0]["threat_level"] == "medium"


class TestExtractTrends:
    def test_empty_research_output_returns_empty_list(self):
        assert extract_trends({}) == []

    def test_extracts_well_formed_entries(self):
        research_output = {
            "key_trends": [
                {"trend": "AI budgeting", "signal_strength": "strong",
                 "implication": "Automate everything", "urgency": "now"},
            ]
        }
        result = extract_trends(research_output)
        assert result == [{
            "name": "AI budgeting",
            "signal_strength": "strong",
            "implication": "Automate everything",
            "urgency": "now",
        }]

    def test_skips_entries_with_no_name(self):
        research_output = {"key_trends": [{"signal_strength": "strong"}]}
        assert extract_trends(research_output) == []

    def test_invalid_signal_strength_defaults_to_moderate(self):
        research_output = {"key_trends": [{"trend": "X", "signal_strength": "explosive"}]}
        result = extract_trends(research_output)
        assert result[0]["signal_strength"] == "moderate"

    def test_non_list_key_trends_returns_empty(self):
        assert extract_trends({"key_trends": {"not": "a list"}}) == []
