"""
Industrial Intelligence API Routes — SureFlow AI Phase 3.

New endpoints for the Industrial Intelligence Platform:
  - Document upload & ingestion pipeline trigger
  - Industrial Copilot (search/chat)
  - Maintenance analysis
  - Lessons Learned analysis
  - Compliance audit
  - Industrial Knowledge Graph queries
  - Industrial MCP (mock CMMS/IoT)
"""
import asyncio
import csv
import io
import json
import os
import uuid
import tempfile
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from core.memory import MemoryStore
from knowledge_graph.industrial_store import industrial_graph
from rag.embeddings import ALL_COLLECTIONS, INDUSTRIAL_COLLECTIONS
from core.mcp import mcp_client
from api.deps import get_current_user, resolve_scope
from models.auth import User

router = APIRouter()

# Uploaded source documents are retained here (ROADMAP §0/§1 — "view source"
# behind a citation) instead of being deleted after processing. Files are
# stored under a per-plant subdirectory so download access is isolated by plant.
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


def _persist_upload_path(run_id: str, suffix: str, plant_id: str) -> str:
    plant_dir = plant_id or "_global"
    d = os.path.join(UPLOAD_DIR, plant_dir)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{run_id}{suffix}")


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class CopilotQueryRequest(BaseModel):
    query: str
    conversation_history: list[dict] = []
    user_role: str = "cto"
    user_plant_id: Optional[str] = None
    target_plant_id: Optional[str] = None


class MaintenanceRequest(BaseModel):
    equipment_tag: str
    analysis_type: str = "full"  # "rca", "prediction", "full"
    incident_context: str = ""
    target_plant_id: Optional[str] = None  # CTO plant-switcher; ignored for plant users


class LessonsLearnedRequest(BaseModel):
    incident_text: str = ""
    equipment_tag: str = ""
    incident_id: str = ""
    analysis_scope: str = "single"  # "single" or "cross_asset"
    target_plant_id: Optional[str] = None


class ComplianceRequest(BaseModel):
    scope: str = "facility"  # "facility", "area", "equipment"
    area_id: str = ""
    equipment_tag: str = ""
    regulation_focus: str = ""
    target_plant_id: Optional[str] = None


class WorkOrderRequest(BaseModel):
    wo_id: str = ""
    title: str
    description: str = ""
    equipment_tag: str
    type: str = "corrective"
    assigned_to: str = ""
    status: str = "open"
    incident_id: str = ""
    target_plant_id: Optional[str] = None


class WorkOrderStatusRequest(BaseModel):
    status: str  # open | planned | in_progress | completed | cancelled


# ─── Document Upload & Ingestion ──────────────────────────────────────────────

def _sync_upload_to_graph(
    doc_result: dict, detected_type: str, run_id: str, file_name: str, graph_result: dict,
    plant_id: str = "",
) -> int:
    """
    Deterministically merge the extracted Equipment entities and the Document
    node from an upload into the Industrial Knowledge Graph, stamped with the
    uploader's `plant_id` so the new nodes stay isolated to that plant.

    kg_agent_process() already runs an LLM pass over the entities, but whether
    it emits Equipment create-operations is discretionary (it only ever sees
    node *counts* as context, never real Area IDs). This makes the write
    deterministic so newly uploaded equipment reliably appears in the
    Equipment / Maintenance / Compliance / Lessons-Learned dropdowns — which
    key off graph nodes, not the vector store that Copilot searches. All
    writes are MERGE-based, so this is safe and idempotent.

    Returns the number of nodes recorded (for the graph_nodes_created count).
    """
    doc_metadata = doc_result.get("doc_metadata", {}) or {}
    entities = doc_result.get("entities", []) or []
    nodes_recorded = 0

    # Resolve a real Area id from the free-text area name the LLM extracted
    # (e.g. "Pump House A" -> "AREA-100"), scoped to the uploader's plant so a
    # same-named area in a different plant can never be matched.
    area_hint = next(iter(doc_metadata.get("applicable_areas") or []), "")
    resolved_area = industrial_graph.find_area_id(area_hint, plant_id or None) or ""

    oem_name = next(
        (e.get("canonical") or e.get("value") for e in entities if e.get("type") == "oem"),
        "",
    )

    # Create an Equipment node for every extracted equipment entity.
    for entity in entities:
        if entity.get("type") != "equipment":
            continue
        tag = entity.get("canonical") or entity.get("value")
        if not tag:
            continue
        try:
            industrial_graph.record_equipment(
                equipment_tag=tag,
                name=entity.get("value", tag),
                area_id=resolved_area,
                oem=oem_name,
                plant_id=plant_id,
            )
            nodes_recorded += 1
        except Exception:
            continue

    # Record the Document node itself, linked to the first applicable asset.
    try:
        applicable_equipment = doc_metadata.get("applicable_equipment") or []
        industrial_graph.record_document(
            doc_id=run_id,
            title=doc_metadata.get("title") or file_name or "Uploaded Document",
            doc_type=detected_type,
            equipment_tag=next(iter(applicable_equipment), ""),
            area_id=resolved_area,
            plant_id=plant_id,
        )
        nodes_recorded += 1
    except Exception as e:
        import logging
        logging.getLogger("companyos.upload").warning(f"Failed to record document in Neo4j: {e}")

    # Invalidate the dashboard stats cache so the new nodes show immediately.
    industrial_graph._stats_cache_dict = {}

    graph_result["nodes_created"] = graph_result.get("nodes_created", 0) + nodes_recorded
    return nodes_recorded


@router.post("/industrial/upload")
async def upload_industrial_document(
    file: UploadFile = File(...),
    doc_type: str = Form("unknown"),
    collection: str = Form(""),
    plant_id: str = Form(""),
    user: User = Depends(get_current_user),
):
    """
    Upload an industrial document and trigger the ingestion pipeline.

    The document goes through:
    1. File save → temp storage
    2. Doc Intelligence Agent → entity extraction
    3. Embed into pgvector (auto-selects collection based on doc_type)
    4. KG Agent → update Neo4j graph

    The document is tagged with the caller's plant so it stays isolated.
    For demo/hackathon purposes, this runs synchronously.
    """
    # Plant users upload only to their own plant; a CTO may target one via the form.
    plant_id = resolve_scope(user, plant_id or None) or ""
    run_id = str(uuid.uuid4())

    # Persist the uploaded file (retained so the source can be viewed later).
    suffix = os.path.splitext(file.filename or "doc.txt")[1]
    tmp_path = _persist_upload_path(run_id, suffix, plant_id)
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        # Step 1: Extract text
        from workflows.industrial_activities import ocr_extract_activity
        extract_result = await ocr_extract_activity(tmp_path, file.filename or "uploaded_doc")

        raw_text = extract_result.get("raw_text", "")
        if not raw_text:
            raise HTTPException(status_code=422, detail="Could not extract text from document")

        # Step 2: Doc Intelligence Agent
        from agents.document_intelligence import doc_intelligence_analyze
        doc_result = await run_in_threadpool(
            doc_intelligence_analyze, raw_text, file_name=file.filename or "uploaded_doc", run_id=run_id
        )

        # Determine collection
        detected_type = doc_result.get("doc_type", doc_type)
        from workflows.industrial_workflows import DOC_TYPE_TO_COLLECTION
        target_collection = collection or DOC_TYPE_TO_COLLECTION.get(detected_type, "10-oem-manuals")

        # Step 3: Embed into pgvector
        embed_result = {}
        try:
            from rag.embeddings import ingest_document
            embed_result = await run_in_threadpool(
                ingest_document, tmp_path, target_collection,
                metadata={"original_name": file.filename, "doc_type": detected_type, "run_id": run_id, "plant_id": plant_id},
            )
        except Exception as e:
            embed_result = {"error": str(e), "chunks_ingested": 0}

        # Step 4: KG Agent → update graph
        graph_result = {}
        entities = doc_result.get("entities", [])
        relationships = doc_result.get("relationships", [])
        if entities or relationships:
            try:
                from agents.knowledge_graph_agent import kg_agent_process
                graph_result = await run_in_threadpool(
                    kg_agent_process,
                    entities=entities,
                    relationships=relationships,
                    doc_metadata=doc_result.get("doc_metadata", {}),
                    run_id=run_id,
                )
            except Exception as e:
                graph_result = {"error": str(e)}

        # Step 4b: deterministically sync extracted Equipment + the Document
        # node into the graph so the dashboards (not just Copilot) see this upload.
        await run_in_threadpool(
            _sync_upload_to_graph, doc_result, detected_type, run_id,
            file.filename or "uploaded_doc", graph_result, plant_id,
        )

        return {
            "status": "completed",
            "run_id": run_id,
            "file_name": file.filename,
            "doc_type": detected_type,
            "collection": target_collection,
            "pages_extracted": extract_result.get("pages", 0),
            "entities_found": len(entities),
            "relationships_found": len(relationships),
            "chunks_embedded": embed_result.get("chunks_ingested", 0),
            "graph_nodes_created": graph_result.get("nodes_created", 0),
            "summary": doc_result.get("summary", ""),
            "doc_metadata": doc_result.get("doc_metadata", {}),
            "source_available": True,
        }
    except Exception:
        # Keep the retained file even if the pipeline fails partway.
        raise


@router.post("/industrial/upload/stream")
async def upload_industrial_document_stream(
    file: UploadFile = File(...),
    doc_type: str = Form("unknown"),
    collection: str = Form(""),
    plant_id: str = Form(""),
    user: User = Depends(get_current_user),
):
    """
    Same ingestion pipeline as /industrial/upload, but streams a real SSE
    progress event (Phase 5) after each pipeline stage actually completes,
    instead of the frontend having to fake the timing with setTimeout.
    The document is tagged with the caller's plant so it stays isolated.
    """
    plant_id = resolve_scope(user, plant_id or None) or ""
    run_id = str(uuid.uuid4())

    # Persist the uploaded file (retained so the source can be viewed later).
    suffix = os.path.splitext(file.filename or "doc.txt")[1]
    tmp_path = _persist_upload_path(run_id, suffix, plant_id)
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    async def event_generator():
        try:
            # Step 1: Extract text
            from workflows.industrial_activities import ocr_extract_activity
            extract_result = await ocr_extract_activity(tmp_path, file.filename or "uploaded_doc")
            raw_text = extract_result.get("raw_text", "")
            if not raw_text:
                yield f"data: {json.dumps({'event': 'error', 'detail': 'Could not extract text from document'})}\n\n"
                return
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'extracting', 'pages': extract_result.get('pages', 0), 'char_count': extract_result.get('char_count', 0)})}\n\n"

            # Step 2: Doc Intelligence Agent
            from agents.document_intelligence import doc_intelligence_analyze
            doc_result = await run_in_threadpool(
                doc_intelligence_analyze, raw_text, file_name=file.filename or "uploaded_doc", run_id=run_id
            )
            entities = doc_result.get("entities", [])
            relationships = doc_result.get("relationships", [])
            detected_type = doc_result.get("doc_type", doc_type)
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'analyzing', 'entities_found': len(entities), 'relationships_found': len(relationships), 'doc_type': detected_type})}\n\n"

            # Determine collection
            from workflows.industrial_workflows import DOC_TYPE_TO_COLLECTION
            target_collection = collection or DOC_TYPE_TO_COLLECTION.get(detected_type, "10-oem-manuals")

            # Step 3: Embed into pgvector
            embed_result = {}
            try:
                from rag.embeddings import ingest_document
                embed_result = await run_in_threadpool(
                    ingest_document, tmp_path, target_collection,
                    metadata={"original_name": file.filename, "doc_type": detected_type, "run_id": run_id, "plant_id": plant_id},
                )
            except Exception as e:
                embed_result = {"error": str(e), "chunks_ingested": 0}
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'embedding', 'chunks_embedded': embed_result.get('chunks_ingested', 0), 'collection': target_collection})}\n\n"

            # Step 4: KG Agent → update graph
            graph_result = {}
            if entities or relationships:
                try:
                    from agents.knowledge_graph_agent import kg_agent_process
                    graph_result = await run_in_threadpool(
                        kg_agent_process,
                        entities=entities,
                        relationships=relationships,
                        doc_metadata=doc_result.get("doc_metadata", {}),
                        run_id=run_id,
                    )
                except Exception as e:
                    graph_result = {"error": str(e)}

            # Step 4b: deterministically sync extracted Equipment + the Document
            # node into the graph so the dashboards (not just Copilot) see this upload.
            await run_in_threadpool(
                _sync_upload_to_graph, doc_result, detected_type, run_id,
                file.filename or "uploaded_doc", graph_result, plant_id,
            )

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'graphing', 'graph_nodes_created': graph_result.get('nodes_created', 0)})}\n\n"

            complete_event = {
                "event": "complete",
                "status": "completed",
                "run_id": run_id,
                "file_name": file.filename,
                "doc_type": detected_type,
                "collection": target_collection,
                "pages_extracted": extract_result.get("pages", 0),
                "entities_found": len(entities),
                "relationships_found": len(relationships),
                "chunks_embedded": embed_result.get("chunks_ingested", 0),
                "graph_nodes_created": graph_result.get("nodes_created", 0),
                "summary": doc_result.get("summary", ""),
                "doc_metadata": doc_result.get("doc_metadata", {}),
            }
            yield f"data: {json.dumps(complete_event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"
        # The uploaded file is intentionally retained (see UPLOAD_DIR) so it can
        # be viewed later via /industrial/documents/{doc_id}/file.

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/industrial/documents/{doc_id}/file")
def get_document_file(doc_id: str, user: User = Depends(get_current_user)):
    """
    Serve the retained source file for an uploaded document. Access is isolated
    by plant: a plant user can only read files under their own plant directory;
    a CTO can read any. `doc_id` is the upload's run_id.
    """
    import glob
    from fastapi.responses import FileResponse

    # Which plant directories may this caller read?
    if user.role == "cto":
        search_dirs = [os.path.join(UPLOAD_DIR, d) for d in os.listdir(UPLOAD_DIR)] if os.path.isdir(UPLOAD_DIR) else []
    else:
        search_dirs = [os.path.join(UPLOAD_DIR, user.plant_id or "_none")]

    for d in search_dirs:
        matches = glob.glob(os.path.join(d, f"{doc_id}.*")) + glob.glob(os.path.join(d, doc_id))
        if matches:
            return FileResponse(matches[0], filename=os.path.basename(matches[0]))
    raise HTTPException(status_code=404, detail="Source document not found or not accessible")


# ─── Industrial Copilot (Search Agent) ────────────────────────────────────────

@router.post("/industrial/copilot")
async def copilot_query(body: CopilotQueryRequest, user: User = Depends(get_current_user)):
    """
    Industrial Copilot — the main conversational interface.
    Performs hybrid search (graph + vector) and synthesizes answers with citations.
    Plant scope is derived from the authenticated user, not the request body.
    """
    resolve_scope(user, body.target_plant_id)  # 403 if plant user targets another plant
    from agents.search_agent import search_copilot_query
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        search_copilot_query,
        query=body.query,
        conversation_history=body.conversation_history,
        run_id=run_id,
        user_role=user.role,
        user_plant_id=user.plant_id,
        target_plant_id=(body.target_plant_id if user.role == "cto" else None),
    )
    return {
        "run_id": run_id,
        **result,
    }


@router.post("/industrial/copilot/stream")
async def copilot_query_stream(body: CopilotQueryRequest, user: User = Depends(get_current_user)):
    """
    Same Copilot answer as /industrial/copilot, but streams stage progress
    events (Phase 5) first so the frontend can show live feedback instead of
    a static spinner. Plant scope is derived from the authenticated user.
    """
    resolve_scope(user, body.target_plant_id)  # 403 if plant user targets another plant
    run_id = str(uuid.uuid4())
    effective_role = user.role
    effective_plant = user.plant_id
    effective_target = body.target_plant_id if user.role == "cto" else None

    async def event_generator():
        stages = [
            ("intent_detection", "Detecting query intent..."),
            ("querying_graph", "Querying knowledge graph..."),
            ("querying_vault", "Searching documents & lessons learned..."),
            ("synthesizing", "Synthesizing answer with citations..."),
        ]
        for stage, label in stages:
            yield f"data: {json.dumps({'event': 'stage', 'stage': stage, 'label': label})}\n\n"
            await asyncio.sleep(0.35)

        try:
            from agents.search_agent import search_copilot_query
            result = await run_in_threadpool(
                search_copilot_query,
                query=body.query,
                conversation_history=body.conversation_history,
                run_id=run_id,
                user_role=effective_role,
                user_plant_id=effective_plant,
                target_plant_id=effective_target,
            )
            yield f"data: {json.dumps({'event': 'complete', 'run_id': run_id, **result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── Maintenance Analysis ────────────────────────────────────────────────────

@router.post("/industrial/maintenance/analyze")
async def maintenance_analysis(body: MaintenanceRequest, user: User = Depends(get_current_user)):
    """
    Run Maintenance Intelligence Agent on specified equipment.
    Performs RCA, failure prediction, and recommends preventive actions.
    """
    from agents.maintenance import maintenance_analyze
    scope = resolve_scope(user, body.target_plant_id)
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        maintenance_analyze,
        equipment_tag=body.equipment_tag,
        analysis_type=body.analysis_type,
        incident_context=body.incident_context,
        run_id=run_id,
        plant_id=scope,
    )
    return {"run_id": run_id, **result}


# ─── Lessons Learned ─────────────────────────────────────────────────────────

@router.post("/industrial/lessons-learned")
async def lessons_learned_analysis(body: LessonsLearnedRequest, user: User = Depends(get_current_user)):
    """
    Run Lessons Learned Agent — extract lessons from incidents,
    generate cross-asset warnings, detect patterns.
    """
    from agents.lessons_learned import lessons_learned_analyze
    scope = resolve_scope(user, body.target_plant_id)
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        lessons_learned_analyze,
        incident_text=body.incident_text,
        equipment_tag=body.equipment_tag,
        incident_id=body.incident_id,
        analysis_scope=body.analysis_scope,
        run_id=run_id,
        plant_id=scope,
    )
    return {"run_id": run_id, **result}


# ─── Compliance Audit ─────────────────────────────────────────────────────────

@router.post("/industrial/compliance/audit")
async def compliance_audit(body: ComplianceRequest, user: User = Depends(get_current_user)):
    """
    Run Compliance Agent — gap analysis, SOP compliance, audit readiness.
    """
    from agents.compliance import compliance_analyze
    plant_scope = resolve_scope(user, body.target_plant_id)
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        compliance_analyze,
        scope=body.scope,
        area_id=body.area_id,
        equipment_tag=body.equipment_tag,
        regulation_focus=body.regulation_focus,
        run_id=run_id,
        plant_id=plant_scope,
    )
    return {"run_id": run_id, **result}


# ─── Industrial Knowledge Graph API ──────────────────────────────────────────

@router.get("/industrial/graph/hierarchy")
def get_plant_hierarchy(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Return the Plant → Area → Equipment tree, scoped to the caller's plant."""
    scope = resolve_scope(user, plant)
    return {"hierarchy": industrial_graph.get_plant_hierarchy(plant_id=scope)}


@router.get("/industrial/graph/equipment")
def get_all_equipment(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Return equipment nodes, scoped to the caller's plant."""
    scope = resolve_scope(user, plant)
    return {"equipment": industrial_graph.get_all_equipment(plant_id=scope)}


@router.get("/industrial/graph/equipment/{tag}")
def get_equipment_detail(tag: str, user: User = Depends(get_current_user)):
    """Full details for a specific equipment tag."""
    detail = industrial_graph.get_equipment_details(tag)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Equipment '{tag}' not found")
    return detail


@router.get("/industrial/graph/equipment/{tag}/timeline")
def get_equipment_timeline(tag: str, limit: int = 20, user: User = Depends(get_current_user)):
    """Asset timeline — incidents, work orders, inspections for an equipment tag."""
    timeline = industrial_graph.get_asset_timeline(tag, limit=limit)
    return {"equipment_tag": tag, "timeline": timeline}


@router.get("/industrial/graph/incidents")
def get_incidents(
    limit: int = 50,
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Return recent incidents, scoped to the caller's plant."""
    scope = resolve_scope(user, plant)
    return {"incidents": industrial_graph.get_all_incidents(limit=limit, plant_id=scope)}


@router.get("/industrial/graph/compliance-gaps/{area_id}")
def get_compliance_gaps(area_id: str, user: User = Depends(get_current_user)):
    """Find compliance gaps in an area — equipment with incidents but no inspections."""
    return {"area_id": area_id, "gaps": industrial_graph.get_compliance_gaps(area_id)}


@router.get("/industrial/graph/overview")
def get_industrial_overview(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Structured node-count stats of the Industrial Knowledge Graph, scoped to
    the caller's plant (matches the frontend's GraphOverview type)."""
    scope = resolve_scope(user, plant)
    return {"overview": industrial_graph.get_graph_stats(plant_id=scope)}


# ─── Industrial KPIs ──────────────────────────────────────────────────────────

@router.get("/industrial/kpis")
def get_industrial_kpis(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """
    High-level industrial KPIs for the dashboard, scoped to the caller's plant.
    Combines graph stats with memory stats.
    """
    scope = resolve_scope(user, plant)
    overview = industrial_graph.get_graph_stats(plant_id=scope)
    memory = MemoryStore()

    # Count operational lessons
    from core.database import SessionLocal
    from models.memory import ReflectionMemory
    db = SessionLocal()
    try:
        lessons_count = db.query(ReflectionMemory).filter(
            ReflectionMemory.category != "agent_failure"
        ).count()
        recent_episodes = db.query(ReflectionMemory).filter(
            ReflectionMemory.category.in_(["safety_incident", "operational_failure"])
        ).count()
    except Exception:
        lessons_count = 0
        recent_episodes = 0
    finally:
        db.close()

    return {
        "graph_overview": overview,
        "lessons_learned_count": lessons_count,
        "safety_incidents": recent_episodes,
    }


# ─── Industrial Vault Stats ──────────────────────────────────────────────────

@router.get("/industrial/vault/stats")
def get_industrial_vault_stats():
    """Return document counts for all Industrial collections."""
    from rag.embeddings import get_vault_stats
    stats = get_vault_stats()
    collections = []
    for name, description in INDUSTRIAL_COLLECTIONS.items():
        collections.append({
            "id": name,
            "name": name,
            "description": description,
            "document_count": stats.get(name, 0),
        })
    return {"collections": collections}


# ─── Work Order API (closed-loop: recommendation → WO → track) ────────────────

@router.get("/industrial/work-orders")
def list_work_orders(
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """List work orders visible to the caller (plant-scoped)."""
    scope = resolve_scope(user, plant)
    return {"work_orders": industrial_graph.get_all_work_orders(plant_id=scope)}


@router.post("/industrial/work-orders")
async def create_work_order(body: WorkOrderRequest, user: User = Depends(get_current_user)):
    """
    Create a work order — records it in the Knowledge Graph, stamped with the
    caller's plant. This is the "act" step that closes the loop from an AI
    maintenance recommendation to a tracked action.
    """
    scope = resolve_scope(user, body.target_plant_id)
    wo_id = body.wo_id or f"WO-{uuid.uuid4().hex[:8].upper()}"

    industrial_graph.record_work_order(
        wo_id=wo_id,
        title=body.title,
        description=body.description,
        equipment_tag=body.equipment_tag,
        wo_type=body.type,
        assigned_to=body.assigned_to,
        status=body.status,
        incident_id=body.incident_id or None,
        plant_id=scope or "",
    )

    memory = MemoryStore()
    memory.save_episodic_industrial(
        "MAINTENANCE",
        f"Work order {wo_id} on {body.equipment_tag}",
        {"wo_id": wo_id, "title": body.title, "equipment_tag": body.equipment_tag},
        equipment_tag=body.equipment_tag,
        context_type="work_order",
        plant_id=scope or "",
    )

    return {"status": "created", "wo_id": wo_id, "equipment_tag": body.equipment_tag}


@router.post("/industrial/work-orders/{wo_id}/status")
def update_work_order_status(wo_id: str, body: WorkOrderStatusRequest, user: User = Depends(get_current_user)):
    """Advance a work order's status (open → in_progress → completed, etc.)."""
    ok = industrial_graph.update_work_order_status(wo_id, body.status)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Work order '{wo_id}' not found")
    industrial_graph._stats_cache_dict = {}
    return {"status": "updated", "wo_id": wo_id, "new_status": body.status}


# ─── Global Search (ROADMAP §1) ──────────────────────────────────────────────

@router.get("/industrial/search")
def global_search(
    q: str = Query(..., min_length=1),
    plant: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Keyword search across equipment, incidents, documents, and lessons — plant-scoped."""
    scope = resolve_scope(user, plant)
    ql = q.strip().lower()

    equipment = [
        e for e in industrial_graph.get_all_equipment(plant_id=scope)
        if ql in f"{e.get('tag', '')} {e.get('name', '')} {e.get('area', '')}".lower()
    ][:12]
    incidents = [
        i for i in industrial_graph.get_all_incidents(limit=100, plant_id=scope)
        if ql in f"{i.get('id', '')} {i.get('title', '')} {i.get('description', '')}".lower()
    ][:12]

    from core.database import SessionLocal
    from models.memory import ReflectionMemory
    from models.vault import VaultDocument
    db = SessionLocal()
    try:
        lq = db.query(ReflectionMemory).filter(
            ReflectionMemory.lesson.ilike(f"%{q}%")
            | ReflectionMemory.failure_reason.ilike(f"%{q}%")
            | ReflectionMemory.task_context.ilike(f"%{q}%")
        )
        if scope:
            lq = lq.filter(ReflectionMemory.plant_id == scope)
        lessons = [
            {"lesson": r.lesson, "equipment_tag": r.equipment_tag, "category": r.category}
            for r in lq.limit(12).all()
        ]

        # Filter the plant scope in Python — portable across JSON/JSONB column types.
        seen: dict = {}
        for row in db.query(VaultDocument).filter(VaultDocument.content.ilike(f"%{q}%")).limit(120).all():
            meta = row.meta_data or {}
            if scope and meta.get("plant_id") != scope:
                continue
            src = meta.get("original_name") or meta.get("source") or "document"
            seen.setdefault(src, {"source": src, "collection": row.collection, "snippet": (row.content or "")[:140]})
        documents = list(seen.values())[:12]
    finally:
        db.close()

    return {"query": q, "equipment": equipment, "incidents": incidents, "documents": documents, "lessons": lessons}


# ─── CSV Export (ROADMAP §1 — dependency-free report export) ──────────────────

def _csv_response(rows: list[dict], columns: list[str], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/industrial/export/equipment.csv")
def export_equipment_csv(plant: Optional[str] = Query(None), user: User = Depends(get_current_user)):
    scope = resolve_scope(user, plant)
    rows = industrial_graph.get_all_equipment(plant_id=scope)
    return _csv_response(rows, ["tag", "name", "area", "asset_class", "created_at"], "equipment.csv")


@router.get("/industrial/export/incidents.csv")
def export_incidents_csv(plant: Optional[str] = Query(None), user: User = Depends(get_current_user)):
    scope = resolve_scope(user, plant)
    rows = industrial_graph.get_all_incidents(limit=500, plant_id=scope)
    return _csv_response(rows, ["id", "title", "severity", "date", "equipment_tag", "equipment_name"], "incidents.csv")


@router.get("/industrial/export/work-orders.csv")
def export_work_orders_csv(plant: Optional[str] = Query(None), user: User = Depends(get_current_user)):
    scope = resolve_scope(user, plant)
    rows = industrial_graph.get_all_work_orders(plant_id=scope)
    return _csv_response(rows, ["wo_id", "title", "type", "status", "equipment_tag", "incident_id", "created_at"], "work_orders.csv")


# ─── Industrial MCP (Mock CMMS/IoT) ──────────────────────────────────────────

@router.get("/industrial/mcp/sensor/{equipment_tag}")
def get_sensor_data(equipment_tag: str):
    """Mock IoT sensor data for an equipment tag."""
    return mcp_client.execute_tool("iot_sensors", "read_sensors", {"equipment_tag": equipment_tag})


@router.post("/industrial/mcp/cmms/work-order")
async def cmms_create_work_order(body: dict):
    """Mock CMMS (SAP/Maximo) work order creation."""
    return mcp_client.execute_tool("cmms", "create_work_order", body)


@router.get("/industrial/mcp/cmms/equipment/{tag}")
def cmms_get_equipment(tag: str):
    """Mock CMMS equipment record lookup."""
    return mcp_client.execute_tool("cmms", "get_equipment", {"equipment_tag": tag})
