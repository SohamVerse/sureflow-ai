"""
Alert generation (ROADMAP §1 — proactive notifications).

Deterministically scans the Industrial Knowledge Graph for alert-worthy
conditions and upserts `Alert` rows. Idempotent via `dedup_key`, so it can be
run on a schedule or on demand without creating duplicates.
"""
from datetime import datetime, timezone
from typing import Optional

from core.database import SessionLocal
from models.alert import Alert
from knowledge_graph.industrial_store import industrial_graph


def _upsert(db, *, plant_id, severity, category, title, message, equipment_tag, source_type, source_id) -> int:
    dedup = f"{category}:{source_id}"
    existing = (
        db.query(Alert)
        .filter(Alert.dedup_key == dedup, Alert.status != "resolved")
        .first()
    )
    if existing:
        # Refresh the open alert's content but keep its status (new/acknowledged).
        existing.title = title
        existing.message = message
        existing.severity = severity
        existing.updated_at = datetime.now(timezone.utc)
        return 0
    db.add(Alert(
        plant_id=plant_id,
        severity=severity,
        category=category,
        title=title,
        message=message,
        equipment_tag=equipment_tag,
        source_type=source_type,
        source_id=source_id,
        dedup_key=dedup,
    ))
    return 1


def generate_alerts(plant_id: Optional[str] = None) -> dict:
    """Scan the graph (optionally scoped to one plant) and upsert open alerts."""
    db = SessionLocal()
    created = 0
    try:
        for inc in industrial_graph.get_unresolved_severe_incidents(plant_id):
            sev = inc.get("severity") or "high"
            created += _upsert(
                db,
                plant_id=inc.get("plant_id"),
                severity=sev,
                category="incident",
                title=f"Unresolved {sev} incident: {inc.get('title', '')}".strip(),
                message=(
                    f"Incident {inc.get('id')} on {inc.get('equipment_tag') or 'an unspecified asset'} "
                    f"has no work order resolving it."
                ),
                equipment_tag=inc.get("equipment_tag"),
                source_type="incident",
                source_id=inc.get("id"),
            )

        for insp in industrial_graph.get_failed_inspections(plant_id):
            created += _upsert(
                db,
                plant_id=insp.get("plant_id"),
                severity="high",
                category="inspection",
                title=f"Failed inspection: {insp.get('title', '')}".strip(),
                message=(
                    f"Inspection {insp.get('id')} on {insp.get('equipment_tag') or 'an unspecified asset'} "
                    f"returned FAIL — remediation required."
                ),
                equipment_tag=insp.get("equipment_tag"),
                source_type="inspection",
                source_id=insp.get("id"),
            )

        db.commit()
    finally:
        db.close()
    return {"created": created}


# Severity ordering for prioritising the digest.
_SEV_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_ACTION_BY_CATEGORY = {
    "incident": "Open or complete a work order to resolve this incident.",
    "inspection": "Schedule remediation and re-inspect the asset.",
    "compliance": "Close the compliance gap before the next audit.",
    "maintenance": "Review the predicted failure and plan preventive maintenance.",
}


def build_digest(plant_id: Optional[str] = None) -> dict:
    """
    Proactive risk digest (ROADMAP §3) — a prioritized "morning briefing".

    Refreshes alerts, then ranks the open ones by severity into a focus list
    with a recommended action for each. Deterministic (no LLM), so it is fast,
    quota-free, and safe to run on a schedule or on every dashboard load.
    """
    generate_alerts(plant_id)  # keep the picture current before summarising

    db = SessionLocal()
    try:
        q = db.query(Alert).filter(Alert.status != "resolved")
        if plant_id:
            q = q.filter(Alert.plant_id == plant_id)
        alerts = q.all()
    finally:
        db.close()

    ordered = sorted(alerts, key=lambda a: (_SEV_RANK.get(a.severity, 9), a.created_at or 0))
    priorities = [
        {
            "rank": i + 1,
            "severity": a.severity,
            "category": a.category,
            "title": a.title,
            "equipment_tag": a.equipment_tag,
            "plant_id": a.plant_id,
            "recommended_action": _ACTION_BY_CATEGORY.get(a.category, "Review and act."),
        }
        for i, a in enumerate(ordered[:10])
    ]

    critical = sum(1 for a in alerts if a.severity == "critical")
    high = sum(1 for a in alerts if a.severity == "high")
    scope_label = plant_id or "all plants"
    if not alerts:
        headline = f"All clear across {scope_label} — no open risks."
    else:
        bits = []
        if critical:
            bits.append(f"{critical} critical")
        if high:
            bits.append(f"{high} high")
        sev_txt = ", ".join(bits) or f"{len(alerts)} open"
        headline = f"{len(alerts)} open risk{'s' if len(alerts) != 1 else ''} across {scope_label} ({sev_txt}) need attention."

    return {
        "scope": plant_id or "global",
        "headline": headline,
        "open_total": len(alerts),
        "critical": critical,
        "high": high,
        "priorities": priorities,
    }
