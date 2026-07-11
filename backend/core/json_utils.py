"""
Robust JSON parsing for LLM output.

LLM backends (notably Gemini "thinking" models such as gemini-3.5-flash) will,
under `response_mime_type=application/json`, still occasionally emit JSON that
is *almost* valid — most commonly missing a closing brace/bracket, a stray
trailing comma, or the whole payload wrapped in a ```json fence. A single such
slip makes a strict `json.loads` raise, which previously collapsed the whole
agent response into an empty fallback (empty entities, no answer, no gaps).

`parse_llm_json` recovers those cases: strict parse first, then markdown-fence
stripping, then a `json_repair` pass that closes unbalanced structures. It
returns a dict on success or None if the content is unsalvageable, letting each
caller keep its own domain-specific fallback for the (now rare) None case.
"""
from __future__ import annotations
import json
import logging
from typing import Optional

logger = logging.getLogger("companyos.json_utils")


def _strip_markdown_fence(content: str) -> str:
    """Remove a leading ```json / ``` fence if the model wrapped its output."""
    stripped = content.strip()
    if stripped.startswith("```"):
        # Drop the opening fence line and any trailing fence.
        stripped = stripped.split("```", 2)[1] if "```" in stripped[3:] else stripped[3:]
        if stripped.startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()


def parse_llm_json(content: str) -> Optional[dict]:
    """
    Best-effort parse of an LLM's JSON output into a dict.

    Order of attempts:
      1. Strict json.loads on the raw content.
      2. Strict json.loads after stripping a ```json fence.
      3. json_repair (closes unbalanced braces/brackets, drops trailing commas,
         recovers truncated tails) on the raw content.

    Returns the parsed dict, or None if every strategy fails or the result
    isn't a non-empty dict (so callers can apply their own fallback).
    """
    if not content or not content.strip():
        return None

    # 1. Strict parse.
    try:
        result = json.loads(content)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Strip a markdown fence and retry strictly.
    fenced = _strip_markdown_fence(content)
    if fenced and fenced != content:
        try:
            result = json.loads(fenced)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. Repair pass — handles missing closing braces, trailing commas, etc.
    try:
        from json_repair import loads as repair_loads
        result = repair_loads(fenced or content)
        if isinstance(result, dict) and result:
            logger.info("Recovered malformed LLM JSON via json_repair.")
            return result
    except Exception as e:  # noqa: BLE001 — repair is best-effort
        logger.warning(f"json_repair could not salvage LLM output: {e}")

    return None
