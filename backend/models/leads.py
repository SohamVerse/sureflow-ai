from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SAEnum, Text, JSON, Uuid
from datetime import datetime, timezone
import uuid
import enum
from core.database import Base


class LeadStatus(str, enum.Enum):
    NEW = "new"
    IN_SEQUENCE = "in_sequence"
    BOOKED = "booked"
    CLOSED = "closed"
    LOST = "lost"


class BuyingStage(str, enum.Enum):
    AWARENESS = "Awareness"
    CONSIDERATION = "Consideration"
    DECISION = "Decision"
    NEGOTIATION = "Negotiation"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SAEnum(LeadStatus), default=LeadStatus.NEW, nullable=False)

    # Contact info
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    company = Column(String(255))
    title = Column(String(255))
    linkedin_url = Column(String(500))

    # Sales intelligence
    buying_stage = Column(SAEnum(BuyingStage), default=BuyingStage.AWARENESS)
    icp_score = Column(Float, default=0.0)     # 0.0 - 10.0 ICP fit score from SDR agent
    touchpoints = Column(Integer, default=0)   # Total contact attempts
    notes = Column(Text)
    meta_data = Column(JSON, default=dict)     # Extra agent-generated data

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    last_contacted_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "status": self.status,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "title": self.title,
            "linkedin_url": self.linkedin_url,
            "buying_stage": self.buying_stage,
            "icp_score": self.icp_score,
            "touchpoints": self.touchpoints,
            "notes": self.notes,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_contacted_at": self.last_contacted_at.isoformat() if self.last_contacted_at else None,
        }
