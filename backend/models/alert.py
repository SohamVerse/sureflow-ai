"""
Alert model — proactive notifications (ROADMAP §1).

Alerts turn the platform from reactive (open a dashboard and ask) into
proactive (it tells you). They are generated deterministically from the
knowledge graph — severe unresolved incidents, failed inspections, compliance
gaps — and are plant-scoped so each plant only sees its own.

`dedup_key` makes generation idempotent: re-running the scan updates the
existing open alert for a signal instead of creating duplicates.
"""
from sqlalchemy import Column, String, Text, DateTime, Uuid
from datetime import datetime, timezone
import uuid

from core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(String(50), nullable=True, index=True)
    severity = Column(String(20), nullable=False, default="medium")   # critical|high|medium|low
    category = Column(String(40), nullable=False)                     # incident|inspection|compliance|maintenance
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False, default="")
    equipment_tag = Column(String(100), nullable=True, index=True)
    source_type = Column(String(40), nullable=True)                  # incident|inspection|prediction|…
    source_id = Column(String(120), nullable=True)
    # new | acknowledged | resolved
    status = Column(String(20), nullable=False, default="new", index=True)
    # Stable identity of the underlying signal, so re-scans upsert instead of dupe.
    dedup_key = Column(String(200), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
