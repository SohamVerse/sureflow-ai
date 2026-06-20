"""
SQLAlchemy models for the EvaluatorBrain (CompanyOS V3.1 Layer 2).

Evaluation columns are split into two groups:
  - Columns computed from data we actually have today (latency, cost,
    schema validity, constitution violations, veto/approval flags).
  - Nullable columns matching the V3.1 spec's full metric taxonomy that
    require ground-truth outcome data this system doesn't capture yet
    (real post engagement, email replies, deal closes). These stay NULL
    until that data exists — never fabricated.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Uuid
from datetime import datetime, timezone
import uuid
from core.database import Base


class Evaluation(Base):
    """One row per evaluated BrainOutput."""
    __tablename__ = "evaluations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    # Correlates every agent call from a single pipeline run (CompanyOS V3.1
    # Layer 4 — see core/telemetry.py). Nullable: calls made before Phase 6
    # or outside a traced pipeline run (e.g. direct /risk/analyze) have none.
    run_id = Column(String(36), nullable=True, index=True)

    # Computed from real data
    latency_ms = Column(Integer, nullable=True)
    cost = Column(Float, default=0.0)
    confidence = Column(Float, nullable=True)
    risk = Column(Float, nullable=True)
    schema_valid = Column(Boolean, default=True)
    constitution_violation_count = Column(Integer, default=0)
    requires_human_approval = Column(Boolean, default=False)
    vetoed = Column(Boolean, default=False)

    # Ground-truth-pending — populated once real outcome tracking exists (Phase 9+)
    research_accuracy = Column(Float, nullable=True)
    ctr_prediction_error = Column(Float, nullable=True)
    open_rate = Column(Float, nullable=True)
    reply_rate = Column(Float, nullable=True)
    close_rate = Column(Float, nullable=True)
    hallucination_score = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    simulation_error = Column(Float, nullable=True)
    brier_score = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    rouge = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "model_name": self.model_name,
            "run_id": self.run_id,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "confidence": self.confidence,
            "risk": self.risk,
            "schema_valid": self.schema_valid,
            "constitution_violation_count": self.constitution_violation_count,
            "requires_human_approval": self.requires_human_approval,
            "vetoed": self.vetoed,
            "research_accuracy": self.research_accuracy,
            "ctr_prediction_error": self.ctr_prediction_error,
            "open_rate": self.open_rate,
            "reply_rate": self.reply_rate,
            "close_rate": self.close_rate,
            "hallucination_score": self.hallucination_score,
            "roi": self.roi,
            "simulation_error": self.simulation_error,
            "brier_score": self.brier_score,
            "mae": self.mae,
            "f1": self.f1,
            "rouge": self.rouge,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Benchmark(Base):
    """Aggregated Evaluation rows for one agent/model pair over a time window."""
    __tablename__ = "benchmarks"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    sample_count = Column(Integer, default=0)

    avg_confidence = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    avg_cost = Column(Float, nullable=True)
    schema_valid_rate = Column(Float, nullable=True)
    constitution_violation_rate = Column(Float, nullable=True)
    veto_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "model_name": self.model_name,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
            "sample_count": self.sample_count,
            "avg_confidence": self.avg_confidence,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_cost": self.avg_cost,
            "schema_valid_rate": self.schema_valid_rate,
            "constitution_violation_rate": self.constitution_violation_rate,
            "veto_rate": self.veto_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentRunError(Base):
    """
    A failure surfaced during one pipeline run. Before Phase 6, the per-node
    try/except messages in agents/graph.py (AgentState["errors"]) were only
    ever visible transiently in a single SSE response — never persisted, so
    "Failures" tracking from the V3.1 spec's Observability layer had no
    historical record. This table is that record.
    """
    __tablename__ = "agent_run_errors"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String(36), nullable=True, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    error_message = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
