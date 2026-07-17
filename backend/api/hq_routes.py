"""
HQ (headquarters) routes — global roll-up and cross-plant comparison.

Mounted at /api/v1/hq. CTO-only. These fan out over every plant and return
comparison-ready shapes for the HQ dashboard and comparison view.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.auth import Location, User
from models.memory import ReflectionMemory
from api.deps import require_cto
from knowledge_graph.industrial_store import industrial_graph

router = APIRouter(prefix="/hq", tags=["hq"])

_STAT_KEYS = ["areas", "equipment", "incidents", "work_orders", "inspections", "documents"]


def _lessons_count(db: Session, plant_id: str) -> int:
    return (
        db.query(ReflectionMemory)
        .filter(ReflectionMemory.category != "agent_failure", ReflectionMemory.plant_id == plant_id)
        .count()
    )


def _plant_metrics(db: Session, p: Location) -> dict:
    stats = industrial_graph.get_graph_stats(plant_id=p.plant_id)
    incidents = industrial_graph.get_all_incidents(limit=500, plant_id=p.plant_id)
    critical = sum(1 for i in incidents if (i.get("severity") or "").lower() == "critical")
    high = sum(1 for i in incidents if (i.get("severity") or "").lower() == "high")
    # Simple risk index: unresolved severe incidents relative to inspection coverage.
    inspections = stats.get("inspections", 0)
    risk_index = round((critical * 3 + high) / (inspections + 1), 2)
    return {
        "plant_id": p.plant_id,
        "name": p.name,
        "location": p.location,
        "status": p.status,
        "stats": stats,
        "critical_incidents": critical,
        "high_incidents": high,
        "lessons_count": _lessons_count(db, p.plant_id),
        "risk_index": risk_index,
    }


@router.get("/overview")
def hq_overview(actor: User = Depends(require_cto), db: Session = Depends(get_db)):
    """Global roll-up across all plants: totals + per-plant summary + worst plant."""
    plants = db.query(Location).order_by(Location.name).all()
    per_plant = [_plant_metrics(db, p) for p in plants]

    totals = {k: 0 for k in _STAT_KEYS}
    for m in per_plant:
        for k in _STAT_KEYS:
            totals[k] += m["stats"].get(k, 0)
    totals["critical_incidents"] = sum(m["critical_incidents"] for m in per_plant)
    totals["lessons"] = sum(m["lessons_count"] for m in per_plant)

    highest_risk = max(per_plant, key=lambda m: m["risk_index"], default=None)
    return {
        "total_plants": len(plants),
        "totals": totals,
        "plants": per_plant,
        "highest_risk_plant": highest_risk["plant_id"] if highest_risk else None,
    }


@router.get("/compare")
def hq_compare(
    plants: str = Query(..., description="Comma-separated plant_ids, e.g. PLANT-001,PLANT-002"),
    actor: User = Depends(require_cto),
    db: Session = Depends(get_db),
):
    """Side-by-side metrics for the requested plants."""
    ids = [x.strip() for x in plants.split(",") if x.strip()]
    rows = []
    for pid in ids:
        p = db.query(Location).filter(Location.plant_id == pid).first()
        if p:
            rows.append(_plant_metrics(db, p))
    return {"comparison": rows}


@router.get("/benchmark")
def hq_benchmark(actor: User = Depends(require_cto), db: Session = Depends(get_db)):
    """
    Rank all plants by a composite reliability score (higher = better).
    Score starts at 100 and is penalized by the plant's risk index and its
    count of critical incidents — a simple, explainable leaderboard.
    """
    plants = db.query(Location).order_by(Location.name).all()
    metrics = [_plant_metrics(db, p) for p in plants]
    for m in metrics:
        m["reliability_score"] = max(0.0, round(100 - m["risk_index"] * 20 - m["critical_incidents"] * 10, 1))
    ranked = sorted(metrics, key=lambda m: m["reliability_score"], reverse=True)
    for i, m in enumerate(ranked):
        m["rank"] = i + 1
    return {"ranking": ranked}
