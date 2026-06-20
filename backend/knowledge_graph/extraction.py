"""
Pure extraction functions for the Strategic Knowledge Graph (CompanyOS V3.1).

Reads the `competitor_intelligence` / `key_trends` fields the RESEARCH brain's
prompt already asks for (see agents/research.py::RESEARCH_SYSTEM_PROMPT) and
normalizes them into a shape graph_store.py can MERGE into Neo4j. No Neo4j
access here — cheap to unit test in isolation (see
backend/tests/test_knowledge_graph_extraction.py).
"""
from __future__ import annotations

VALID_THREAT_LEVELS = {"low", "medium", "high"}
VALID_SIGNAL_STRENGTHS = {"weak", "moderate", "strong"}


def extract_competitors(research_output: dict) -> list[dict]:
    """
    Returns a list of {name, recent_moves, weakness, threat_level} dicts.
    Skips entries with no usable name — local models don't always honor the
    prompt's schema, so this is defensive rather than assuming clean input
    (same principle as core/brain.py::parse_brain_output's coercion).
    """
    raw_list = research_output.get("competitor_intelligence", [])
    if not isinstance(raw_list, list):
        return []

    competitors = []
    for entry in raw_list:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("competitor", "")).strip()
        if not name:
            continue
        threat_level = str(entry.get("threat_level", "medium")).lower()
        if threat_level not in VALID_THREAT_LEVELS:
            threat_level = "medium"
        competitors.append({
            "name": name,
            "recent_moves": str(entry.get("recent_moves", "")),
            "weakness": str(entry.get("weakness", "")),
            "threat_level": threat_level,
        })
    return competitors


def extract_trends(research_output: dict) -> list[dict]:
    """Returns a list of {name, signal_strength, implication, urgency} dicts."""
    raw_list = research_output.get("key_trends", [])
    if not isinstance(raw_list, list):
        return []

    trends = []
    for entry in raw_list:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("trend", "")).strip()
        if not name:
            continue
        signal_strength = str(entry.get("signal_strength", "moderate")).lower()
        if signal_strength not in VALID_SIGNAL_STRENGTHS:
            signal_strength = "moderate"
        trends.append({
            "name": name,
            "signal_strength": signal_strength,
            "implication": str(entry.get("implication", "")),
            "urgency": str(entry.get("urgency", "")),
        })
    return trends
