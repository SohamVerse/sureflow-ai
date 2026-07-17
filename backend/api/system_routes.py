"""
System / observability routes (ROADMAP §1 — AI Quality & Cost panel).

Surfaces the data the evaluator already collects on every agent call
(confidence, latency, cost, schema-validity, human-approval flags) so the AI
system's quality and spend are visible instead of hidden in the DB.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, cast, Integer
from sqlalchemy.orm import Session

from core.database import get_db
from models.auth import User
from api.deps import get_current_user
from evaluation.models import Evaluation

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ai-quality")
def ai_quality(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Per-agent quality/cost aggregates + the most recent runs."""
    rows = (
        db.query(
            Evaluation.agent_id,
            func.count(Evaluation.id).label("runs"),
            func.avg(Evaluation.confidence).label("avg_confidence"),
            func.avg(Evaluation.latency_ms).label("avg_latency"),
            func.sum(Evaluation.cost).label("total_cost"),
            func.sum(cast(Evaluation.requires_human_approval, Integer)).label("approvals"),
            func.sum(cast(Evaluation.schema_valid, Integer)).label("valid"),
            func.max(Evaluation.model_name).label("model"),
        )
        .group_by(Evaluation.agent_id)
        .all()
    )

    agents = []
    for r in rows:
        runs = r.runs or 0
        agents.append({
            "agent_id": r.agent_id,
            "model": r.model,
            "runs": runs,
            "avg_confidence": round(r.avg_confidence or 0, 1),
            "avg_latency_ms": int(r.avg_latency or 0),
            "total_cost": round(r.total_cost or 0, 6),
            "human_approvals": int(r.approvals or 0),
            "schema_valid_rate": round(100 * (r.valid or 0) / runs) if runs else 100,
        })
    agents.sort(key=lambda a: a["agent_id"])

    recent = db.query(Evaluation).order_by(Evaluation.created_at.desc()).limit(15).all()
    total_runs = sum(a["runs"] for a in agents)
    totals = {
        "total_runs": total_runs,
        "total_cost": round(sum(a["total_cost"] for a in agents), 6),
        "avg_latency_ms": int(sum(a["avg_latency_ms"] * a["runs"] for a in agents) / total_runs) if total_runs else 0,
    }
    return {"agents": agents, "recent": [e.to_dict() for e in recent], "totals": totals}
