"""
MetaLearningBrain — CompanyOS V3.1 Layer 3.

Owns the versioned heuristic weight set injected into CMO/Email prompts. Per
the V3.1 spec: "MUST NOT modify prompts directly... tunes internal float
weights mathematically... stored in Postgres, versioned, easily rolled back."

Weight *values* are proposed explicitly (via propose_update, with a reason)
rather than auto-tuned from Benchmark data — see the module docstring in
meta_learning/validation.py and the Phase 5 plan for why: there's no real
engagement signal yet to learn from (MCP is mocked, no outcome tracking).
GET /api/v1/heuristics/review-context (api/routes.py) surfaces the real
operational data a human needs to make that call.
"""
from __future__ import annotations
import logging

from sqlalchemy import func

from core.database import SessionLocal
from meta_learning.models import HeuristicVersion
from meta_learning.defaults import DEFAULT_HEURISTICS
from meta_learning.validation import validate_weights, format_heuristics_for_prompt

logger = logging.getLogger("companyos.meta_learning")


class MetaLearningBrain:
    """Reads/writes versioned heuristic weights. Always queries fresh (no
    in-process caching) so a propose_update/rollback is immediately reflected
    in the next CMO/Email prompt, without a process restart."""

    def get_active_heuristics(self) -> dict:
        """Load the active heuristic weight set, seeding version 1 from
        DEFAULT_HEURISTICS if the table is empty."""
        db = SessionLocal()
        try:
            active = (
                db.query(HeuristicVersion)
                .filter(HeuristicVersion.active == True)  # noqa: E712
                .order_by(HeuristicVersion.version.desc())
                .first()
            )
            if active:
                return active.weights

            db.add(HeuristicVersion(
                version=1,
                weights=DEFAULT_HEURISTICS,
                change_reason="Initial seed from V3.1 spec defaults",
                updated_by="system",
                active=True,
            ))
            db.commit()
            return DEFAULT_HEURISTICS
        finally:
            db.close()

    def get_as_prompt_context(self) -> str:
        """Formatted block for injection into CMO/Email system prompts."""
        return format_heuristics_for_prompt(self.get_active_heuristics())

    def propose_update(self, weights: dict, reason: str, updated_by: str = "system") -> dict:
        """Create a new heuristic version and make it active. Never mutates a
        prior version — append-only, same pattern as the Constitution."""
        errors = validate_weights(weights)
        if errors:
            raise ValueError(f"Invalid heuristic weights: {'; '.join(errors)}")

        db = SessionLocal()
        try:
            current_max = db.query(func.max(HeuristicVersion.version)).scalar() or 0
            db.query(HeuristicVersion).filter(HeuristicVersion.active == True).update(  # noqa: E712
                {"active": False}
            )
            new_version = HeuristicVersion(
                version=current_max + 1,
                weights=weights,
                change_reason=reason,
                updated_by=updated_by,
                active=True,
            )
            db.add(new_version)
            db.commit()
            db.refresh(new_version)
            logger.info("New heuristic version %d by %s: %s", new_version.version, updated_by, reason)
            return new_version.to_dict()
        finally:
            db.close()

    def rollback_to_version(self, version: int) -> dict:
        """Reactivate a prior version. Does not delete or rewrite history."""
        db = SessionLocal()
        try:
            target = db.query(HeuristicVersion).filter(HeuristicVersion.version == version).first()
            if not target:
                raise ValueError(f"No heuristic version {version} found")

            db.query(HeuristicVersion).filter(HeuristicVersion.active == True).update(  # noqa: E712
                {"active": False}
            )
            target.active = True
            db.commit()
            db.refresh(target)
            logger.info("Rolled back heuristics to version %d", version)
            return target.to_dict()
        finally:
            db.close()

    def get_history(self) -> list[dict]:
        """All heuristic versions, most recent first."""
        db = SessionLocal()
        try:
            rows = db.query(HeuristicVersion).order_by(HeuristicVersion.version.desc()).all()
            return [r.to_dict() for r in rows]
        finally:
            db.close()


meta_learning_brain = MetaLearningBrain()
