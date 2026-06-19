from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum, JSON, Uuid, Integer, Float, Boolean
from datetime import datetime, timezone
import uuid
import enum
from core.database import Base


class PipelineStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    VETOED = "vetoed"          # NEW: Risk Brain vetoed this item


class AgentType(str, enum.Enum):
    CEO = "CEO"
    CMO = "CMO"
    RESEARCH = "RESEARCH"
    SDR = "SDR"
    AE = "AE"
    ANALYST = "ANALYST"
    EMAIL = "EMAIL"
    RISK = "RISK"              # NEW: Risk Analysis Brain


class PipelineItem(Base):
    __tablename__ = "pipeline_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(SAEnum(AgentType), nullable=False)
    status = Column(SAEnum(PipelineStatus), default=PipelineStatus.PENDING, nullable=False)

    # Content fields
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    platform = Column(String(100))
    stage = Column(String(100))
    meta_data = Column(JSON, default=dict)

    # Brain Decision Framework fields
    confidence = Column(Integer, nullable=True)            # 0-100
    risk_score = Column(Integer, nullable=True)            # 0-100 (from Risk Brain)
    risk_level = Column(String(20), nullable=True)         # low|medium|high|critical
    reasoning = Column(Text, nullable=True)                # Agent's internal reasoning
    alternatives = Column(JSON, default=list)              # Other options evaluated
    approval_tier = Column(String(30), nullable=True)      # AUTO_APPROVE|MANAGER|CEO
    debate_log = Column(JSON, default=list)                # Debate Engine notes
    constitution_violations = Column(JSON, default=list)   # Any violations detected
    approval_required = Column(Boolean, default=False)     # Needs human review

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "status": self.status,
            "title": self.title,
            "content": self.content,
            "platform": self.platform,
            "stage": self.stage,
            "meta_data": self.meta_data,
            # Brain Decision Framework fields
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives or [],
            "approval_tier": self.approval_tier,
            "debate_log": self.debate_log or [],
            "constitution_violations": self.constitution_violations or [],
            "approval_required": self.approval_required,
            # Timestamps
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
        }
