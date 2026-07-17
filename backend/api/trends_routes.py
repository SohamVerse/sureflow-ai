"""
KPI trends routes (ROADMAP §1) — mounted at /api/v1/industrial/kpis.

Captures point-in-time KPI snapshots and returns them as a time series for the
Trends charts. Plant-scoped: a plant user sees their plant's history; a CTO sees
the global roll-up (or a single plant when the switcher passes `plant`).
"""
from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.auth import User
from models.kpi_snapshot import KpiSnapshot
from models.memory import ReflectionMemory
from models.alert import Alert
from api.deps import get_current_user, resolve_scope
from knowledge_graph.industrial_store import industrial_graph

router = APIRouter(prefix="/industrial/kpis", tags=["trends"])


def _capture(db: Session, plant_id: Optional[str]) -> KpiSnapshot:
    stats = industrial_graph.get_graph_stats(plant_id=plant_id)
    lessons_q = db.query(ReflectionMemory).filter(ReflectionMemory.category != "agent_failure")
    alerts_q = db.query(Alert).filter(Alert.status == "new")
    if plant_id:
        lessons_q = lessons_q.filter(ReflectionMemory.plant_id == plant_id)
        alerts_q = alerts_q.filter(Alert.plant_id == plant_id)
    row = KpiSnapshot(
        plant_id=plant_id,
        equipment=stats.get("equipment", 0),
        incidents=stats.get("incidents", 0),
        work_orders=stats.get("work_orders", 0),
        inspections=stats.get("inspections", 0),
        documents=stats.get("documents", 0),
        lessons=lessons_q.count(),
        open_alerts=alerts_q.count(),
    )
    db.add(row)
    return row


@router.post("/snapshot")
def snapshot(plant: Optional[str] = Query(None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Capture the current KPIs for the caller's scope (schedule this daily/weekly)."""
    scope = resolve_scope(user, plant)
    _capture(db, scope)
    db.commit()
    return {"status": "captured", "scope": scope or "global"}


@router.get("/trends")
def trends(
    days: int = Query(120),
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the KPI time series for the caller's scope."""
    scope = resolve_scope(user, plant)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = db.query(KpiSnapshot).filter(KpiSnapshot.created_at >= since)
    q = q.filter(KpiSnapshot.plant_id == scope) if scope else q.filter(KpiSnapshot.plant_id.is_(None))
    rows = q.order_by(KpiSnapshot.created_at).all()
    return {
        "scope": scope or "global",
        "snapshots": [
            {
                "date": r.created_at.date().isoformat() if r.created_at else None,
                "equipment": r.equipment,
                "incidents": r.incidents,
                "work_orders": r.work_orders,
                "inspections": r.inspections,
                "documents": r.documents,
                "lessons": r.lessons,
                "open_alerts": r.open_alerts,
            }
            for r in rows
        ],
    }
