"""
Alert routes (ROADMAP §1) — mounted at /api/v1/alerts.

Plant-scoped: a plant user sees only their plant's alerts; a CTO sees all
(or a single plant when the switcher passes `plant`). Scope derives from the
JWT via resolve_scope — never from a client body field.
"""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from core.database import get_db
from models.alert import Alert
from models.auth import User
from api.deps import get_current_user, resolve_scope
from core.alerts import generate_alerts, build_digest

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/digest")
def digest(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Proactive prioritized risk briefing for the caller's scope."""
    scope = resolve_scope(user, plant)
    return build_digest(plant_id=scope)


def _alert_out(a: Alert) -> dict:
    return {
        "id": str(a.id),
        "plant_id": a.plant_id,
        "severity": a.severity,
        "category": a.category,
        "title": a.title,
        "message": a.message,
        "equipment_tag": a.equipment_tag,
        "source_type": a.source_type,
        "source_id": a.source_id,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _scoped_query(db: Session, user: User, plant: Optional[str]):
    scope = resolve_scope(user, plant)  # plant user → their plant; CTO → plant or None(all)
    q = db.query(Alert)
    if scope:
        q = q.filter(Alert.plant_id == scope)
    return q


@router.get("")
def list_alerts(
    plant: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List alerts visible to the caller, newest first."""
    q = _scoped_query(db, user, plant)
    if status_filter:
        q = q.filter(Alert.status == status_filter)
    rows = q.order_by(Alert.created_at.desc()).limit(200).all()
    return {"alerts": [_alert_out(a) for a in rows]}


@router.get("/count")
def alert_count(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Count of open (new) alerts — for the sidebar bell badge."""
    q = _scoped_query(db, user, plant).filter(Alert.status == "new")
    return {"count": q.count()}


@router.post("/generate")
def generate(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-scan the graph and upsert alerts for the caller's scope."""
    scope = resolve_scope(user, plant)
    result = generate_alerts(plant_id=scope)
    return result


def _get_owned_alert(db: Session, user: User, alert_id: str) -> Alert:
    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Alert not found")
    a = db.query(Alert).filter(Alert.id == aid).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    # Plant users may only touch their own plant's alerts.
    if user.role != "cto" and a.plant_id != user.plant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your plant's alert")
    return a


@router.post("/{alert_id}/ack")
def acknowledge(alert_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = _get_owned_alert(db, user, alert_id)
    a.status = "acknowledged"
    a.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "acknowledged", "id": alert_id}


@router.post("/{alert_id}/resolve")
def resolve(alert_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = _get_owned_alert(db, user, alert_id)
    a.status = "resolved"
    a.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "resolved", "id": alert_id}
