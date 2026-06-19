from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Uuid
from datetime import datetime, timezone
import uuid
from core.database import Base


class EpisodicMemory(Base):
    """A past task run and its outcome, scoped to a single agent."""
    __tablename__ = "episodic_memories"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, index=True)
    task = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=False)
    confidence = Column(Integer, default=50)
    risk_level = Column(String(20), default="medium")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class ReflectionMemory(Base):
    """A lesson learned from a failure or sub-optimal outcome, scoped to a single agent."""
    __tablename__ = "reflection_memories"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, index=True)
    task_context = Column(String(300), nullable=False)
    failure_reason = Column(Text, nullable=False)
    lesson = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
