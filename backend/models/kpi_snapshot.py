"""
KpiSnapshot — point-in-time KPI capture for trends over time (ROADMAP §1).

Every metric on the dashboards is otherwise a live count with no history. A
periodic snapshot (per plant, plus a global roll-up with plant_id=NULL) lets the
UI draw incident-rate / MTBF / equipment trends over weeks and months.
"""
from sqlalchemy import Column, String, Integer, DateTime, Uuid
from datetime import datetime, timezone
import uuid

from core.database import Base


class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(String(50), nullable=True, index=True)  # NULL = global roll-up
    equipment = Column(Integer, default=0)
    incidents = Column(Integer, default=0)
    work_orders = Column(Integer, default=0)
    inspections = Column(Integer, default=0)
    documents = Column(Integer, default=0)
    lessons = Column(Integer, default=0)
    open_alerts = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
