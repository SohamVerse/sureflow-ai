from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Uuid
from datetime import datetime, timezone
import uuid
from core.database import Base


class HeuristicVersion(Base):
    """
    Append-only, immutable record of a heuristic weight set (CompanyOS V3.1
    Layer 3 — MetaLearningBrain). Never updated in place — a change creates a
    new version row and flips `active`, same pattern as
    models/constitution.py::ConstitutionVersion.
    """
    __tablename__ = "heuristic_versions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(Integer, nullable=False, unique=True)
    weights = Column(JSON, nullable=False)
    change_reason = Column(String(500), default="")
    updated_by = Column(String(255), default="system")
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "version": self.version,
            "weights": self.weights,
            "change_reason": self.change_reason,
            "updated_by": self.updated_by,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
