"""
FastAPI REST API routes for SureFlow AI — shared/core endpoints.
Industrial Intelligence Platform endpoints live in api/industrial_routes.py.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.memory import MemoryStore
from evaluation.models import Evaluation, Benchmark, AgentRunError
from evaluation.evaluator import evaluator, AGENT_MODELS
from evaluation.metrics import compute_campaign_summary
from skill_registry.registry import skill_registry

router = APIRouter()


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class ReflectionRequest(BaseModel):
    agent_id: str
    task_context: str
    failure_reason: str
    lesson: str


# ─── System Health ─────────────────────────────────────────────────────────────

@router.get("/health")
def health_check():
    return {"status": "online", "service": "SureFlow AI", "version": "2.0.0"}


@router.get("/agents/status")
def agent_status():
    """Return current model config and status for all Industrial Intelligence Brains."""
    from core.config import settings
    return {
        "agents": [
            {"id": "DOC_INTELLIGENCE", "name": "Document Intelligence Brain", "model": settings.DOC_INTELLIGENCE_MODEL, "status": "idle", "role": "Document Processing & Entity Extraction"},
            {"id": "KG_AGENT",         "name": "Knowledge Graph Brain",       "model": settings.KG_AGENT_MODEL,         "status": "idle", "role": "Entity Resolution & Graph Updates"},
            {"id": "SEARCH_AGENT",     "name": "Industrial Copilot",          "model": settings.SEARCH_AGENT_MODEL,     "status": "idle", "role": "Hybrid Search & Synthesis"},
            {"id": "MAINTENANCE",      "name": "Maintenance Intelligence",    "model": settings.MAINTENANCE_MODEL,      "status": "idle", "role": "RCA & Failure Prediction"},
            {"id": "LESSONS_LEARNED",  "name": "Lessons Learned Brain",       "model": settings.LESSONS_LEARNED_MODEL,  "status": "idle", "role": "Incident Analysis & Warnings"},
            {"id": "COMPLIANCE",       "name": "Compliance Brain",            "model": settings.COMPLIANCE_MODEL,       "status": "idle", "role": "Regulatory Gap Analysis"},
        ]
    }


# ─── Memory API ────────────────────────────────────────────────────────────────

@router.get("/memory/{agent_id}")
def get_agent_memory(agent_id: str):
    """Return memory summary for a specific agent brain."""
    memory = MemoryStore()
    return memory.get_memory_summary(agent_id.upper())


@router.post("/memory/reflection")
def save_reflection(body: ReflectionRequest):
    """Manually save a reflection (lesson learned) for an agent."""
    memory = MemoryStore()
    memory.save_reflection(
        agent_id=body.agent_id.upper(),
        task=body.task_context,
        failure_reason=body.failure_reason,
        lesson=body.lesson,
    )
    return {"status": "saved", "agent_id": body.agent_id.upper()}


# ─── EvaluatorBrain ────────────────────────────────────────────────────────────

@router.get("/evaluations")
def get_evaluations(agent_id: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """Return recent BrainOutput evaluations, optionally filtered by agent."""
    query = db.query(Evaluation)
    if agent_id:
        query = query.filter(Evaluation.agent_id == agent_id.upper())
    rows = query.order_by(Evaluation.created_at.desc()).limit(limit).all()
    return [r.to_dict() for r in rows]


@router.get("/benchmarks")
def get_benchmarks(agent_id: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """Return recent benchmark snapshots, optionally filtered by agent."""
    query = db.query(Benchmark)
    if agent_id:
        query = query.filter(Benchmark.agent_id == agent_id.upper())
    rows = query.order_by(Benchmark.created_at.desc()).limit(limit).all()
    return [r.to_dict() for r in rows]


@router.post("/benchmarks/generate")
def generate_benchmarks():
    """
    On-demand benchmark generation for every live agent/model pair — the same
    work the daily Temporal schedule does (workflows/cron_workflow.py), useful
    for testing/demo without waiting a day.
    """
    generated, skipped = [], []
    for agent_id, model_name in AGENT_MODELS.items():
        benchmark = evaluator.generate_benchmark(agent_id, model_name)
        (generated if benchmark else skipped).append(f"{agent_id}/{model_name}")
    return {"generated": generated, "skipped": skipped}


# ─── Observability (distributed tracing correlation) ──────────────────────────

@router.get("/observability/campaigns/{run_id}")
def get_campaign(run_id: str, db: Session = Depends(get_db)):
    """
    Every Evaluation + AgentRunError for one run, plus a computed summary.
    The same run_id tags this run's trace in Jaeger (core/telemetry.py), so a
    trace and its cost/latency/error data are cross-referenceable.
    """
    evaluations = (
        db.query(Evaluation)
        .filter(Evaluation.run_id == run_id)
        .order_by(Evaluation.created_at.asc())
        .all()
    )
    errors = (
        db.query(AgentRunError)
        .filter(AgentRunError.run_id == run_id)
        .order_by(AgentRunError.created_at.asc())
        .all()
    )
    if not evaluations and not errors:
        raise HTTPException(status_code=404, detail=f"No data found for run_id {run_id}")

    evaluation_dicts = [e.to_dict() for e in evaluations]
    return {
        "run_id": run_id,
        "summary": compute_campaign_summary(evaluation_dicts),
        "evaluations": evaluation_dicts,
        "errors": [e.to_dict() for e in errors],
    }


# ─── Trusted Skill Registry ─────────────────────────────────────────────────────

@router.get("/skills/reputation")
def get_skill_reputations():
    """
    Every tracked skill's trust_score/avg_latency_ms/failure_rate, each tagged
    `is_mocked` — the mocked CMMS/IoT Sensor platforms in core/mcp.py reflect
    "the mock always succeeds," not real-world reliability. `ollama.embed` is
    the one genuinely real skill.
    """
    return {"skills": skill_registry.get_all_reputations()}


@router.get("/skills/reputation/{skill_name}")
def get_skill_reputation(skill_name: str):
    """One skill's reputation detail."""
    return skill_registry.get_reputation(skill_name)


@router.get("/skills/recommend")
def recommend_skill(category: str):
    """The registry's highest-trust pick for a capability category (e.g. cmms, iot, embedding).
    Returns null if no skill in that category has any recorded executions yet."""
    return {"category": category, "recommended_skill": skill_registry.recommend(category)}
