"""
TrustedSkillRegistry — CompanyOS V3.1 Layer 6.

Wraps tool/skill executions with timing + success/failure logging, so
reputation (trust_score, latency, failure_rate) is computed from real
execution history rather than declared. Two kinds of skills are registered
today:
  - The 4 MCP platforms in core/mcp.py (linkedin, hubspot, instagram, gmail)
    — fully MOCKED, can never fail. Their reputation honestly reflects "the
    mock always succeeds instantly," not real-world reliability. Always
    tagged `is_mocked: true` so nothing downstream mistakes this for real
    data. Real OAuth integrations are a separate, much bigger effort.
  - `ollama.embed` (rag/embeddings.py) — a genuinely real, already-exercised
    skill (real network calls to a real local service), giving the registry
    at least one skill with authentic operational variance.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Callable

from core.database import SessionLocal
from skill_registry.models import SkillExecution
from skill_registry.metrics import compute_reputation

logger = logging.getLogger("companyos.skill_registry")

# core/mcp.py's MCPServer is fully mocked — never a real OAuth/API call.
MOCKED_SKILLS = {
    "mcp.linkedin.post",
    "mcp.linkedin.search_leads",
    "mcp.hubspot.create_contact",
    "mcp.hubspot.update_deal",
    "mcp.instagram.post_reel",
    "mcp.gmail.send_email",
}

# Maps a skill to the capability category it serves, for recommend().
SKILL_CATEGORIES = {
    "mcp.linkedin.post": "social_post",
    "mcp.instagram.post_reel": "social_post",
    "mcp.hubspot.create_contact": "crm",
    "mcp.hubspot.update_deal": "crm",
    "mcp.gmail.send_email": "email",
    "ollama.embed": "embedding",
}


class TrustedSkillRegistry:
    def execute(self, skill_name: str, fn: Callable[[], Any]) -> Any:
        """
        Executes fn(), logging one SkillExecution row with timing and
        success/failure. Re-raises any exception from fn() — this is an
        observability wrapper, not an error-handling one; callers keep their
        own error semantics.
        """
        start = time.perf_counter()
        try:
            result = fn()
            self._log(skill_name, success=True, latency_ms=self._elapsed_ms(start))
            return result
        except Exception as e:
            self._log(skill_name, success=False, latency_ms=self._elapsed_ms(start), error_message=str(e))
            raise

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return max(0, round((time.perf_counter() - start) * 1000))

    def _log(self, skill_name: str, success: bool, latency_ms: int, error_message: str | None = None) -> None:
        db = SessionLocal()
        try:
            db.add(SkillExecution(
                skill_name=skill_name, success=success, latency_ms=latency_ms, error_message=error_message,
            ))
            db.commit()
        except Exception:
            logger.exception("Failed to log skill execution for %s", skill_name)
        finally:
            db.close()

    def get_reputation(self, skill_name: str) -> dict:
        db = SessionLocal()
        try:
            rows = db.query(SkillExecution).filter(SkillExecution.skill_name == skill_name).all()
        finally:
            db.close()
        reputation = compute_reputation([{"success": r.success, "latency_ms": r.latency_ms} for r in rows])
        return {"skill_name": skill_name, "is_mocked": skill_name in MOCKED_SKILLS, **reputation}

    def get_all_reputations(self) -> list[dict]:
        db = SessionLocal()
        try:
            skill_names = [r[0] for r in db.query(SkillExecution.skill_name).distinct().all()]
        finally:
            db.close()
        return [self.get_reputation(name) for name in skill_names]

    def recommend(self, category: str) -> str | None:
        """
        The highest-trust_score skill in `category` with at least one
        recorded execution (ties broken by lowest avg_latency_ms). Returns
        None if no skill in that category has been executed yet — there's
        nothing honest to recommend from zero data.
        """
        candidates = [name for name, cat in SKILL_CATEGORIES.items() if cat == category]
        reputations = [self.get_reputation(name) for name in candidates]
        reputations = [r for r in reputations if r["total_calls"] > 0]
        if not reputations:
            return None
        best = min(reputations, key=lambda r: (-r["trust_score"], r["avg_latency_ms"] or float("inf")))
        return best["skill_name"]


skill_registry = TrustedSkillRegistry()
