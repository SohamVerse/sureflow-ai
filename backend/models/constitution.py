from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Uuid
from datetime import datetime, timezone
import uuid
from core.database import Base


class ConstitutionVersion(Base):
    """
    Append-only, immutable record of a company constitution ruleset.
    Never updated in place — a change creates a new version row and flips `active`.
    """
    __tablename__ = "constitution_versions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(Integer, nullable=False, unique=True)
    sha256 = Column(String(64), nullable=False)
    content = Column(JSON, nullable=False)
    approved_by = Column(String(255), default="system")
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
