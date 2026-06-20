"""
SQLAlchemy model for the TrustedSkillRegistry (CompanyOS V3.1 Layer 6).
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Uuid
from datetime import datetime, timezone
import uuid
from core.database import Base


class SkillExecution(Base):
    """One row per execution of a registered skill (MCP tool call, embedding
    call, etc.) — see skill_registry/registry.py::TrustedSkillRegistry.execute()."""
    __tablename__ = "skill_executions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = Column(String(100), nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    error_message = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "skill_name": self.skill_name,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
