"""
Seed synthetic KPI history so the Trends charts have a story to show.

Generates ~12 weekly snapshots for each plant (and a global roll-up with
plant_id=NULL) with a gently improving trend — incidents/open-alerts trending
down, work orders completed trending up. Real deployments would instead capture
one snapshot on a daily/weekly schedule via POST /industrial/kpis/snapshot.

Usage:
    cd backend
    .venv\\Scripts\\python.exe scripts/seed_kpi_snapshots.py
"""
import sys
import os
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import create_tables, SessionLocal
from models.kpi_snapshot import KpiSnapshot

WEEKS = 12

# (plant_id, base_equipment, start_incidents, end_incidents)
PLANTS = [
    ("PLANT-001", 8, 9, 5),
    ("PLANT-002", 4, 6, 3),
]


def _series(start: int, end: int, i: int, n: int) -> int:
    frac = i / max(1, n - 1)
    val = start + (end - start) * frac + random.uniform(-0.6, 0.6)
    return max(0, round(val))


def seed():
    create_tables()
    db = SessionLocal()
    try:
        db.query(KpiSnapshot).delete()  # idempotent — rebuild the demo history
        now = datetime.now(timezone.utc)
        for i in range(WEEKS):
            ts = now - timedelta(weeks=(WEEKS - 1 - i))
            globals_row = dict(equipment=0, incidents=0, work_orders=0, inspections=0, documents=0, lessons=0, open_alerts=0)
            for plant_id, base_eq, inc_start, inc_end in PLANTS:
                incidents = _series(inc_start, inc_end, i, WEEKS)
                equipment = base_eq + round(i / 4)  # slow growth as assets are onboarded
                work_orders = _series(4, 9, i, WEEKS)
                inspections = _series(2, 6, i, WEEKS)
                documents = base_eq + i
                lessons = _series(1, 4, i, WEEKS)
                open_alerts = _series(inc_start - 2, max(0, inc_end - 3), i, WEEKS)
                row = dict(equipment=equipment, incidents=incidents, work_orders=work_orders,
                           inspections=inspections, documents=documents, lessons=lessons, open_alerts=open_alerts)
                db.add(KpiSnapshot(plant_id=plant_id, created_at=ts, **row))
                for k in globals_row:
                    globals_row[k] += row[k]
            db.add(KpiSnapshot(plant_id=None, created_at=ts, **globals_row))
        db.commit()
        print(f"[SEED] Created {WEEKS} weekly snapshots x ({len(PLANTS)} plants + global).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
