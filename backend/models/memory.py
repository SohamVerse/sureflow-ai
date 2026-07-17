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
    # Industrial extension: tie episodes to specific equipment
    equipment_tag = Column(String(100), nullable=True, index=True)
    # "agent_run" (default), "maintenance", "inspection", "incident_rca"
    context_type = Column(String(50), nullable=True, default="agent_run")
    # Multi-location: which plant this episode belongs to (NULL = global/legacy)
    plant_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class ReflectionMemory(Base):
    """A lesson learned from a failure or sub-optimal outcome, scoped to a single agent."""
    __tablename__ = "reflection_memories"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, index=True)
    task_context = Column(String(300), nullable=False)
    failure_reason = Column(Text, nullable=False)
    lesson = Column(Text, nullable=False)
    # Industrial extension: tie reflections to equipment and incidents
    equipment_tag = Column(String(100), nullable=True, index=True)
    incident_id = Column(String(100), nullable=True)
    # "agent_failure" (default), "operational_failure", "safety_incident", "near_miss"
    category = Column(String(50), nullable=True, default="agent_failure")
    # Where the lesson originated: "agent", "incident_report", "capa", "operator_feedback"
    source = Column(String(50), nullable=True, default="agent")
    # Multi-location: which plant this lesson belongs to (NULL = global/legacy)
    plant_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

