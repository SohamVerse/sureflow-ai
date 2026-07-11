"""
Industrial Intelligence API Routes — SureFlow OS Phase 3.

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
import json
import os
import uuid
import tempfile
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from core.memory import MemoryStore
from knowledge_graph.industrial_store import industrial_graph
from rag.embeddings import ALL_COLLECTIONS, INDUSTRIAL_COLLECTIONS
from core.mcp import mcp_client

router = APIRouter()


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class CopilotQueryRequest(BaseModel):
    query: str
    conversation_history: list[dict] = []


class MaintenanceRequest(BaseModel):
    equipment_tag: str
    analysis_type: str = "full"  # "rca", "prediction", "full"
    incident_context: str = ""


class LessonsLearnedRequest(BaseModel):
    incident_text: str = ""
    equipment_tag: str = ""
    incident_id: str = ""
    analysis_scope: str = "single"  # "single" or "cross_asset"


class ComplianceRequest(BaseModel):
    scope: str = "facility"  # "facility", "area", "equipment"
    area_id: str = ""
    equipment_tag: str = ""
    regulation_focus: str = ""


class WorkOrderRequest(BaseModel):
    wo_id: str = ""
    title: str
    description: str = ""
    equipment_tag: str
    type: str = "corrective"
    assigned_to: str = ""
    status: str = "open"
    incident_id: str = ""


# ─── Document Upload & Ingestion ──────────────────────────────────────────────

def _sync_upload_to_graph(
    doc_result: dict, detected_type: str, run_id: str, file_name: str, graph_result: dict
) -> int:
    """
    Deterministically merge the extracted Equipment entities and the Document
    node from an upload into the Industrial Knowledge Graph.

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
    # (e.g. "Pump House A" -> "AREA-100") so new nodes join the hierarchy.
    area_hint = next(iter(doc_metadata.get("applicable_areas") or []), "")
    resolved_area = industrial_graph.find_area_id(area_hint) or area_hint or ""

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
        )
        nodes_recorded += 1
    except Exception as e:
        import logging
        logging.getLogger("companyos.upload").warning(f"Failed to record document in Neo4j: {e}")

    # Invalidate the dashboard stats cache so the new nodes show immediately.
    industrial_graph._stats_cache = None
    industrial_graph._stats_cache_at = 0.0

    graph_result["nodes_created"] = graph_result.get("nodes_created", 0) + nodes_recorded
    return nodes_recorded


@router.post("/industrial/upload")
async def upload_industrial_document(
    file: UploadFile = File(...),
    doc_type: str = Form("unknown"),
    collection: str = Form(""),
):
    """
    Upload an industrial document and trigger the ingestion pipeline.

    The document goes through:
    1. File save → temp storage
    2. Doc Intelligence Agent → entity extraction
    3. Embed into pgvector (auto-selects collection based on doc_type)
    4. KG Agent → update Neo4j graph

    For demo/hackathon purposes, this runs synchronously.
    In production, this would trigger a Temporal workflow.
    """
    run_id = str(uuid.uuid4())

    # Save uploaded file
    suffix = os.path.splitext(file.filename or "doc.txt")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

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
                metadata={"original_name": file.filename, "doc_type": detected_type, "run_id": run_id},
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
            file.filename or "uploaded_doc", graph_result,
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
        }
    finally:
        os.unlink(tmp_path)


@router.post("/industrial/upload/stream")
async def upload_industrial_document_stream(
    file: UploadFile = File(...),
    doc_type: str = Form("unknown"),
    collection: str = Form(""),
):
    """
    Same ingestion pipeline as /industrial/upload, but streams a real SSE
    progress event (Phase 5) after each pipeline stage actually completes,
    instead of the frontend having to fake the timing with setTimeout.
    """
    run_id = str(uuid.uuid4())

    suffix = os.path.splitext(file.filename or "doc.txt")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

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
                    metadata={"original_name": file.filename, "doc_type": detected_type, "run_id": run_id},
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
                file.filename or "uploaded_doc", graph_result,
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
        finally:
            os.unlink(tmp_path)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── Industrial Copilot (Search Agent) ────────────────────────────────────────

@router.post("/industrial/copilot")
async def copilot_query(body: CopilotQueryRequest):
    """
    Industrial Copilot — the main conversational interface.
    Performs hybrid search (graph + vector) and synthesizes answers with citations.
    """
    from agents.search_agent import search_copilot_query
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        search_copilot_query,
        query=body.query,
        conversation_history=body.conversation_history,
        run_id=run_id,
    )
    return {
        "run_id": run_id,
        **result,
    }


@router.post("/industrial/copilot/stream")
async def copilot_query_stream(body: CopilotQueryRequest):
    """
    Same Copilot answer as /industrial/copilot, but streams stage progress
    events (Phase 5) first so the frontend can show live feedback instead of
    a static spinner. search_copilot_query() itself is a single LLM call that
    gathers graph + vector context internally, so the stages below describe
    what that call is doing rather than being separately-timed sub-calls —
    the pacing gives the presenter/user something to read while it runs.
    """
    run_id = str(uuid.uuid4())

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
            )
            yield f"data: {json.dumps({'event': 'complete', 'run_id': run_id, **result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── Maintenance Analysis ────────────────────────────────────────────────────

@router.post("/industrial/maintenance/analyze")
async def maintenance_analysis(body: MaintenanceRequest):
    """
    Run Maintenance Intelligence Agent on specified equipment.
    Performs RCA, failure prediction, and recommends preventive actions.
    """
    from agents.maintenance import maintenance_analyze
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        maintenance_analyze,
        equipment_tag=body.equipment_tag,
        analysis_type=body.analysis_type,
        incident_context=body.incident_context,
        run_id=run_id,
    )
    return {"run_id": run_id, **result}


# ─── Lessons Learned ─────────────────────────────────────────────────────────

@router.post("/industrial/lessons-learned")
async def lessons_learned_analysis(body: LessonsLearnedRequest):
    """
    Run Lessons Learned Agent — extract lessons from incidents,
    generate cross-asset warnings, detect patterns.
    """
    from agents.lessons_learned import lessons_learned_analyze
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        lessons_learned_analyze,
        incident_text=body.incident_text,
        equipment_tag=body.equipment_tag,
        incident_id=body.incident_id,
        analysis_scope=body.analysis_scope,
        run_id=run_id,
    )
    return {"run_id": run_id, **result}


# ─── Compliance Audit ─────────────────────────────────────────────────────────

@router.post("/industrial/compliance/audit")
async def compliance_audit(body: ComplianceRequest):
    """
    Run Compliance Agent — gap analysis, SOP compliance, audit readiness.
    """
    from agents.compliance import compliance_analyze
    run_id = str(uuid.uuid4())
    result = await run_in_threadpool(
        compliance_analyze,
        scope=body.scope,
        area_id=body.area_id,
        equipment_tag=body.equipment_tag,
        regulation_focus=body.regulation_focus,
        run_id=run_id,
    )
    return {"run_id": run_id, **result}


# ─── Industrial Knowledge Graph API ──────────────────────────────────────────

@router.get("/industrial/graph/hierarchy")
def get_plant_hierarchy():
    """Return the full Plant → Area → Equipment tree."""
    return {"hierarchy": industrial_graph.get_plant_hierarchy()}


@router.get("/industrial/graph/equipment")
def get_all_equipment():
    """Return all equipment nodes."""
    return {"equipment": industrial_graph.get_all_equipment()}


@router.get("/industrial/graph/equipment/{tag}")
def get_equipment_detail(tag: str):
    """Full details for a specific equipment tag."""
    detail = industrial_graph.get_equipment_details(tag)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Equipment '{tag}' not found")
    return detail


@router.get("/industrial/graph/equipment/{tag}/timeline")
def get_equipment_timeline(tag: str, limit: int = 20):
    """Asset timeline — incidents, work orders, inspections for an equipment tag."""
    timeline = industrial_graph.get_asset_timeline(tag, limit=limit)
    return {"equipment_tag": tag, "timeline": timeline}


@router.get("/industrial/graph/incidents")
def get_incidents(limit: int = 50):
    """Return recent incidents."""
    return {"incidents": industrial_graph.get_all_incidents(limit=limit)}


@router.get("/industrial/graph/compliance-gaps/{area_id}")
def get_compliance_gaps(area_id: str):
    """Find compliance gaps in an area — equipment with incidents but no inspections."""
    return {"area_id": area_id, "gaps": industrial_graph.get_compliance_gaps(area_id)}


@router.get("/industrial/graph/overview")
def get_industrial_overview():
    """Structured node-count stats of the Industrial Knowledge Graph (matches
    the frontend's GraphOverview type — plants/areas/equipment/etc as numbers,
    not the prompt-context text summary used internally by agents)."""
    return {"overview": industrial_graph.get_graph_stats()}


# ─── Industrial KPIs ──────────────────────────────────────────────────────────

@router.get("/industrial/kpis")
def get_industrial_kpis():
    """
    High-level industrial KPIs for the dashboard.
    Combines graph stats with memory stats.
    """
    overview = industrial_graph.get_graph_stats()
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


# ─── Work Order API ───────────────────────────────────────────────────────────

@router.post("/industrial/work-orders")
async def create_work_order(body: WorkOrderRequest):
    """
    Create a work order — records it in the Knowledge Graph and
    optionally triggers maintenance analysis.
    """
    wo_id = body.wo_id or f"WO-{uuid.uuid4().hex[:8].upper()}"

    # Record in graph
    industrial_graph.record_work_order(
        wo_id=wo_id,
        title=body.title,
        description=body.description,
        equipment_tag=body.equipment_tag,
        wo_type=body.type,
        assigned_to=body.assigned_to,
        status=body.status,
        incident_id=body.incident_id or None,
    )

    # Record in memory
    memory = MemoryStore()
    memory.save_episodic_industrial(
        "MAINTENANCE",
        f"Work order {wo_id} on {body.equipment_tag}",
        {"wo_id": wo_id, "title": body.title, "equipment_tag": body.equipment_tag},
        equipment_tag=body.equipment_tag,
        context_type="work_order",
    )

    return {
        "status": "created",
        "wo_id": wo_id,
        "equipment_tag": body.equipment_tag,
    }


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
