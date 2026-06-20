"""
FastAPI REST API routes for CompanyOS V2.
Connects the Next.js frontend to the V2 LangGraph backend.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db, SessionLocal
from core.memory import MemoryStore
from core.constitution import constitution, DEFAULT_CONSTITUTION
from models.pipeline import PipelineItem, PipelineStatus, AgentType
from models.leads import Lead, LeadStatus, BuyingStage
from agents.graph import run_pipeline, stream_custom_pipeline, stream_pipeline
from rag.embeddings import ingest_document, get_vault_stats, query_collection, VAULT_COLLECTIONS

router = APIRouter()


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class RunPipelineRequest(BaseModel):
    goal: str
    lead_data: Optional[dict] = None


class CustomPipelineRequest(BaseModel):
    graph_json: str
    goal: str
    lead_data: Optional[dict] = None


class UpdateStatusRequest(BaseModel):
    status: str


class CreateLeadRequest(BaseModel):
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None


class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    buying_stage: Optional[str] = None
    icp_score: Optional[float] = None
    notes: Optional[str] = None


class ReflectionRequest(BaseModel):
    agent_id: str
    task_context: str
    failure_reason: str
    lesson: str


# ─── System Health ─────────────────────────────────────────────────────────────

@router.get("/health")
def health_check():
    return {"status": "online", "service": "CompanyOS V2", "version": "2.0.0"}


@router.get("/agents/status")
def agent_status():
    """Return current model config and status for all V2 Brains."""
    from core.config import settings
    return {
        "agents": [
            {"id": "CEO",      "name": "CEO Brain",             "model": settings.CEO_MODEL,       "status": "idle", "role": "Executive Orchestrator"},
            {"id": "CMO",      "name": "CMO Brain",             "model": settings.CMO_MODEL,       "status": "idle", "role": "Content & Marketing"},
            {"id": "RESEARCH", "name": "Research Analyst Brain","model": settings.RESEARCH_MODEL,  "status": "idle", "role": "Market Intelligence"},
            {"id": "SDR",      "name": "SDR Brain",             "model": settings.SDR_MODEL,       "status": "idle", "role": "Lead Qualification"},
            {"id": "AE",       "name": "Account Executive Brain","model": settings.AE_MODEL,       "status": "idle", "role": "Deal Closing"},
            {"id": "RISK",     "name": "Risk Analysis Brain",   "model": settings.RISK_MODEL,      "status": "idle", "role": "Risk & Veto Authority"},
            {"id": "EMAIL",    "name": "Email Marketing Brain", "model": settings.EMAIL_MODEL,     "status": "idle", "role": "Outreach & Nurture"},
            {"id": "ANALYST",  "name": "Business Analyst Brain","model": settings.ANALYST_MODEL,   "status": "idle", "role": "KPI & Analytics"},
        ]
    }


# ─── Pipeline (Content) ────────────────────────────────────────────────────────

def _extract_approval_tier(brain_output: dict) -> str:
    """Determine approval tier from V2 brain output confidence and risk."""
    confidence = brain_output.get("confidence", 50)
    risk = brain_output.get("risk_level", "medium")
    if risk in ("high", "critical") or confidence < 40:
        return "CEO_APPROVAL"
    elif risk == "medium" or confidence < 70:
        return "MANAGER_APPROVAL"
    return "AUTO_APPROVE"


def persist_pipeline_results(final_state: dict, goal: str) -> list[str]:
    """
    Persist CMO/Research/Risk outputs from a completed pipeline run as PipelineItems.
    Shared by the interactive SSE endpoint (trigger_pipeline) and the
    Temporal-scheduled cron workflow (workflows/activities.py).
    """
    db = SessionLocal()
    created_items = []
    try:
        risk_output = final_state.get("risk_output", {})
        risk_score = risk_output.get("risk_dimensions", {}).get("campaign_failure_probability")
        debate_log = final_state.get("debate_log", [])
        constitution_violations = final_state.get("constitution_violations", [])

        # Persist CMO output
        if final_state.get("cmo_output"):
            cmo = final_state["cmo_output"]
            approval_tier = _extract_approval_tier(cmo)
            # Auto-veto if Risk Brain vetoed
            is_vetoed = risk_output.get("veto_decision", {}).get("vetoed", False)
            status = PipelineStatus.VETOED if is_vetoed else PipelineStatus.PENDING

            item = PipelineItem(
                agent_type=AgentType.CMO,
                status=status,
                title=cmo.get("hook", goal)[:499],
                content=cmo.get("body", ""),
                platform=cmo.get("platform", "LinkedIn"),
                stage=cmo.get("buying_stage", cmo.get("stage", "Awareness")),
                meta_data=cmo,
                confidence=cmo.get("confidence"),
                risk_score=risk_score,
                risk_level=cmo.get("risk_level"),
                reasoning=cmo.get("reasoning", ""),
                alternatives=cmo.get("alternatives", []),
                approval_tier=approval_tier,
                debate_log=debate_log,
                constitution_violations=constitution_violations,
                approval_required=approval_tier != "AUTO_APPROVE" or is_vetoed,
            )
            db.add(item)
            created_items.append("CMO content")

        # Persist Research output
        if final_state.get("research_output"):
            res = final_state["research_output"]
            approval_tier = _extract_approval_tier(res)
            item = PipelineItem(
                agent_type=AgentType.RESEARCH,
                status=PipelineStatus.PENDING,
                title=res.get("executive_summary", res.get("summary", goal))[:499],
                content=json.dumps(res),
                platform="Internal",
                stage="Research",
                meta_data=res,
                confidence=res.get("confidence"),
                risk_level=res.get("risk_level"),
                reasoning=res.get("reasoning", ""),
                alternatives=res.get("alternatives", []),
                approval_tier=approval_tier,
                approval_required=False,
            )
            db.add(item)
            created_items.append("Research report")

        # Persist Risk output
        if final_state.get("risk_output") and risk_output.get("go_no_go"):
            item = PipelineItem(
                agent_type=AgentType.RISK,
                status=PipelineStatus.PENDING,
                title=f"Risk Analysis: {risk_output.get('risk_summary', goal)[:450]}",
                content=json.dumps(risk_output),
                platform="Internal",
                stage="Risk Assessment",
                meta_data=risk_output,
                confidence=risk_output.get("confidence"),
                risk_score=risk_score,
                risk_level=risk_output.get("risk_level"),
                reasoning=risk_output.get("reasoning", ""),
                approval_required=risk_output.get("veto_decision", {}).get("vetoed", False),
            )
            db.add(item)
            created_items.append("Risk report")

        db.commit()
    finally:
        db.close()

    return created_items


@router.post("/pipeline/run")
async def trigger_pipeline(body: RunPipelineRequest):
    """Trigger the V2 CEO Brain and stream outputs back via SSE."""

    async def event_generator():
        final_state = {}

        async for event in stream_pipeline(body.goal, body.lead_data):
            update = event.get("update", {}) or {}
            for key, val in update.items():
                if isinstance(val, list):
                    final_state[key] = final_state.get(key, []) + val
                elif isinstance(val, dict):
                    final_state[key] = {**(final_state.get(key, {})), **val}
                else:
                    final_state[key] = val

            def _enc(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                if hasattr(obj, "dict"):
                    return obj.dict()
                return str(obj)

            yield f"data: {json.dumps(event, default=_enc)}\n\n"

        created_items = persist_pipeline_results(final_state, body.goal)

        complete_event = {
            "event": "complete",
            "success": True,
            "items_created": created_items,
            "agents_run": final_state.get("completed_agents", []),
            "errors": final_state.get("errors", []),
            "debate_log": final_state.get("debate_log", []),
            "approval_required": final_state.get("approval_required", False),
            "risk_veto": final_state.get("risk_output", {}).get("veto_decision", {}),
        }
        yield f"data: {json.dumps(complete_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/pipeline/custom")
async def trigger_custom_pipeline(body: CustomPipelineRequest):
    """Run a user-defined agent graph and stream outputs back via SSE."""
    
    async def event_generator():
        final_state = {}
        async for event in stream_custom_pipeline(body.graph_json, body.goal, body.lead_data):
            if event.get("event") == "error":
                yield f"data: {json.dumps(event)}\n\n"
                return
                
            update = event.get("update", {}) or {}
            for key, val in update.items():
                if isinstance(val, list):
                    final_state[key] = final_state.get(key, []) + val
                elif isinstance(val, dict):
                    final_state[key] = {**(final_state.get(key, {})), **val}
                else:
                    final_state[key] = val
                    
            def _custom_encoder(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                if hasattr(obj, "dict"):
                    return obj.dict()
                return str(obj)

            yield f"data: {json.dumps(event, default=_custom_encoder)}\n\n"

        db = SessionLocal()
        created_items = []
        try:
            if final_state.get("cmo_output"):
                cmo = final_state["cmo_output"]
                item = PipelineItem(
                    agent_type=AgentType.CMO,
                    status=PipelineStatus.PENDING,
                    title=cmo.get("hook", body.goal)[:499],
                    content=cmo.get("body", ""),
                    platform=cmo.get("platform", "LinkedIn"),
                    stage=cmo.get("stage", "Awareness"),
                    meta_data=cmo,
                )
                db.add(item)
                created_items.append("CMO content")

            if final_state.get("research_output"):
                res = final_state["research_output"]
                item = PipelineItem(
                    agent_type=AgentType.RESEARCH,
                    status=PipelineStatus.PENDING,
                    title=res.get("summary", body.goal)[:499],
                    content=json.dumps(res),
                    platform="Internal",
                    stage="Research",
                    meta_data=res,
                )
                db.add(item)
                created_items.append("Research report")

            db.commit()
        finally:
            db.close()

        complete_event = {
            "event": "complete",
            "success": True,
            "items_created": created_items,
            "agents_run": [],
            "errors": []
        }
        yield f"data: {json.dumps(complete_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/pipeline/items")
def get_pipeline_items(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch pipeline items, optionally filtered by status."""
    query = db.query(PipelineItem)
    if status:
        query = query.filter(PipelineItem.status == status)
    items = query.order_by(PipelineItem.created_at.desc()).all()
    return [item.to_dict() for item in items]


@router.patch("/pipeline/items/{item_id}/status")
def update_item_status(item_id: uuid.UUID, body: UpdateStatusRequest, db: Session = Depends(get_db)):
    """Approve, reject, or update the status of a pipeline item."""
    item = db.query(PipelineItem).filter(PipelineItem.id == str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")

    try:
        item.status = PipelineStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    if body.status == "approved":
        item.approved_at = datetime.now(timezone.utc)

    db.commit()
    return item.to_dict()


@router.post("/pipeline/items/{item_id}/post")
def post_pipeline_item_mcp(item_id: uuid.UUID, db: Session = Depends(get_db)):
    """Mock endpoint to publish content via MCP to Instagram/LinkedIn/X."""
    item = db.query(PipelineItem).filter(PipelineItem.id == str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
        
    if item.status != PipelineStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Item must be APPROVED before posting")
        
    # TODO: Here we would trigger the actual MCP Server client (e.g., mcp-social-media)
    print(f"[MCP] Publishing '{item.title}' to {item.platform} via MCP Server...")
    
    item.status = PipelineStatus.POSTED
    item.posted_at = datetime.now(timezone.utc)
    
    db.commit()
    return {"status": "success", "message": "Published via MCP", "item": item.to_dict()}


@router.get("/pipeline/kpis")
def get_kpis(db: Session = Depends(get_db)):
    """Return high-level KPIs for the Command Center dashboard."""
    from sqlalchemy import func
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    posts_this_week = db.query(PipelineItem).filter(
        PipelineItem.status == PipelineStatus.POSTED,
        PipelineItem.posted_at >= week_ago,
    ).count()

    active_leads = db.query(Lead).filter(
        Lead.status.in_([LeadStatus.NEW, LeadStatus.IN_SEQUENCE])
    ).count()

    booked_calls = db.query(Lead).filter(Lead.status == LeadStatus.BOOKED).count()
    pending_review = db.query(PipelineItem).filter(PipelineItem.status == PipelineStatus.PENDING).count()

    return {
        "posts_this_week": posts_this_week,
        "active_leads": active_leads,
        "calls_booked": booked_calls,
        "pending_review": pending_review,
    }


# ─── Leads (CRM) ──────────────────────────────────────────────────────────────

@router.get("/leads")
def get_leads(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    leads = query.order_by(Lead.created_at.desc()).all()
    return [lead.to_dict() for lead in leads]


@router.post("/leads")
def create_lead(body: CreateLeadRequest, db: Session = Depends(get_db)):
    lead = Lead(**body.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead.to_dict()


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: uuid.UUID, body: UpdateLeadRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = body.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(lead, key, val)

    db.commit()
    return lead.to_dict()


@router.post("/leads/{lead_id}/score")
async def score_lead(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    """Trigger SDR agent to score a specific lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    from agents.sales import sdr_score_lead
    result = sdr_score_lead(lead.to_dict())

    lead.icp_score = result.get("icp_score", lead.icp_score)
    lead.buying_stage = result.get("buying_stage", lead.buying_stage)
    lead.touchpoints = (lead.touchpoints or 0) + 1
    lead.last_contacted_at = datetime.now(timezone.utc)
    lead.meta_data = {**(lead.meta_data or {}), "last_sdr_output": result}

    db.commit()
    return {"lead": lead.to_dict(), "sdr_result": result}


# ─── Knowledge Vault ──────────────────────────────────────────────────────────

@router.get("/vault/stats")
def vault_stats():
    """Return document counts for all Knowledge Vault collections."""
    stats = get_vault_stats()
    collections = []
    for name, description in VAULT_COLLECTIONS.items():
        collections.append({
            "id": name,
            "name": name,
            "description": description,
            "document_count": stats.get(name, 0),
        })
    return {"collections": collections}


@router.post("/vault/ingest")
async def ingest_to_vault(
    collection: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload and embed a document into a Knowledge Vault collection."""
    import tempfile, os
    if collection not in VAULT_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown collection: {collection}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = ingest_document(tmp_path, collection, metadata={"original_name": file.filename})
    finally:
        os.unlink(tmp_path)

    return result


@router.post("/vault/query")
def query_vault(body: dict):
    """Semantic search across a Knowledge Vault collection."""
    collection = body.get("collection")
    query = body.get("query")
    n_results = body.get("n_results", 5)

    if not collection or not query:
        raise HTTPException(status_code=400, detail="collection and query are required")

    results = query_collection(collection, query, n_results)
    return {"results": results}


# ─── Analytics ────────────────────────────────────────────────────────────────

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Aggregate telemetry for the Analytics page."""
    from sqlalchemy import func
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total_posts = db.query(PipelineItem).filter(PipelineItem.status == PipelineStatus.POSTED).count()
    total_leads = db.query(Lead).count()
    qualified_leads = db.query(Lead).filter(Lead.icp_score >= 7.0).count()
    replied_leads = db.query(Lead).filter(Lead.touchpoints > 0).count()

    qualified_rate = round((qualified_leads / total_leads * 100), 1) if total_leads > 0 else 0
    reply_rate = round((replied_leads / total_leads * 100), 1) if total_leads > 0 else 0

    weekly_posts = db.query(PipelineItem).filter(
        PipelineItem.status == PipelineStatus.POSTED,
        PipelineItem.posted_at >= week_ago,
    ).count()

    return {
        "weekly_reach": weekly_posts * 150,
        "qualified_rate": qualified_rate,
        "reply_rate": reply_rate,
        "total_leads": total_leads,
        "total_posts": total_posts,
        "weekly_posts": weekly_posts,
    }


# ─── V2: Memory API ───────────────────────────────────────────────────────────

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


# ─── V2: Constitution API ─────────────────────────────────────────────────────

@router.get("/constitution")
def get_constitution():
    """Return the active company constitution."""
    return {"constitution": DEFAULT_CONSTITUTION}


@router.get("/constitution/validate")
def validate_with_constitution(text: str, agent_id: str = ""):
    """Validate a text snippet against the company constitution."""
    violations = constitution.validate({"text": text}, agent_id=agent_id)
    return {
        "passed": not constitution.has_blockers(violations),
        "violations": [{"rule": v.rule, "severity": v.severity, "details": v.details, "fix": v.suggested_fix} for v in violations],
        "summary": constitution.summarize(violations),
    }


# ─── V2: Approval Center ─────────────────────────────────────────────────────

@router.get("/approvals")
def get_pending_approvals(db: Session = Depends(get_db)):
    """Return all items that require human approval (Approval Center)."""
    items = db.query(PipelineItem).filter(
        PipelineItem.approval_required == True,
        PipelineItem.status.in_([PipelineStatus.PENDING, PipelineStatus.VETOED])
    ).order_by(PipelineItem.created_at.desc()).all()
    return [item.to_dict() for item in items]


@router.post("/approvals/{item_id}/approve")
def approve_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    """Approve a flagged item (overrides veto or manager-required flags)."""
    item = db.query(PipelineItem).filter(PipelineItem.id == str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.status = PipelineStatus.APPROVED
    item.approval_required = False
    item.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "approved", "item": item.to_dict()}


@router.post("/approvals/{item_id}/reject")
def reject_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    """Reject a flagged item."""
    item = db.query(PipelineItem).filter(PipelineItem.id == str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.status = PipelineStatus.REJECTED
    item.approval_required = False
    db.commit()
    return {"status": "rejected", "item": item.to_dict()}


# ─── V2: Risk Analysis ────────────────────────────────────────────────────────

@router.post("/risk/analyze")
async def analyze_risk(body: dict):
    """Run the Risk Analysis Brain on a given campaign context."""
    from agents.risk import risk_analyze
    campaign_context = body.get("campaign_context", {})
    instruction = body.get("instruction", "")
    result = risk_analyze(campaign_context, {}, instruction)
    return result
