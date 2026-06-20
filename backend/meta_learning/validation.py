"""
Pure functions for the MetaLearningBrain (CompanyOS V3.1 Layer 3).

No DB/network access — cheap to unit test in isolation (see
backend/tests/test_heuristics_validation.py). DB/ORM concerns live in
meta_learning/brain.py.
"""
from __future__ import annotations

MIN_WEIGHT = 0.0
MAX_WEIGHT = 2.0

# Short tactical descriptions for the weights the spec names explicitly.
# Custom/unknown weight keys are still rendered (with a generic label), so
# this isn't a hard whitelist — just better prompt context where we have it.
TACTIC_DESCRIPTIONS = {
    "social_proof": "lean into testimonials, customer logos, and social proof",
    "urgency": "urgency/scarcity framing — higher means more time-pressure language",
    "discount_bias": "discount/promo-driven framing — higher means more price-led hooks",
    "founder_tone": "first-person, founder-voice authenticity over polished corporate copy",
    "ugc_weight": "user-generated-content style over produced/branded style",
}


def validate_weights(weights: dict) -> list[str]:
    """
    Validate a proposed heuristic weight set. Returns a list of human-readable
    error strings (empty list means valid).
    """
    errors = []
    if not weights:
        errors.append("weights must be a non-empty dict")
        return errors

    for key, value in weights.items():
        if not isinstance(key, str) or not key:
            errors.append(f"invalid weight key: {key!r}")
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{key}: value must be a number, got {type(value).__name__}")
            continue
        if not (MIN_WEIGHT <= value <= MAX_WEIGHT):
            errors.append(f"{key}: {value} is outside the valid range [{MIN_WEIGHT}, {MAX_WEIGHT}]")

    return errors


def format_heuristics_for_prompt(weights: dict) -> str:
    """Render the active heuristic weights as a short block for injection into
    CMO/Email system prompts."""
    if not weights:
        return "No tuned heuristics on record — use your default judgment."

    lines = ["=== TUNED HEURISTIC WEIGHTS (0.0-2.0 scale; 1.0 = neutral) ==="]
    for key, value in weights.items():
        description = TACTIC_DESCRIPTIONS.get(key, "custom tactical weight")
        lines.append(f"  • {key} = {value} — {description}")
    lines.append("=== END HEURISTIC WEIGHTS ===")
    return "\n".join(lines)
