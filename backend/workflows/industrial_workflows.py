"""
Industrial Temporal Workflows — SureFlow AI Phase 3.

Deterministic workflow definitions for industrial intelligence pipelines.
Activities (non-deterministic LLM/DB work) live in industrial_activities.py.

Workflows:
  1. DocumentIngestionWorkflow — Upload → OCR → Doc Intelligence → Embed → Graph
  2. MaintenanceLifecycleWorkflow — Work Order → Graph + Memory → RCA → Alert
  3. LessonsLearnedWorkflow — Incident → Lessons → Reflection Memory
"""
from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.industrial_activities import (
        ocr_extract_activity,
        doc_intelligence_activity,
        embed_and_store_activity,
        update_industrial_graph_activity,
        maintenance_analysis_activity,
        record_work_order_activity,
        lessons_learned_activity,
        compliance_audit_activity,
    )


# ── Data Classes (workflow inputs) ────────────────────────────────────────────

@dataclass
class DocumentIngestionInput:
    file_path: str
    file_name: str
    doc_type: str = "unknown"  # oem_manual, sop, compliance_regulation, etc.
    collection: str = ""       # pgvector collection to store in (auto-detected if empty)
    run_id: str = ""


@dataclass
class MaintenanceInput:
    equipment_tag: str
    work_order_data: dict | None = None
    analysis_type: str = "full"
    incident_context: str = ""
    run_id: str = ""


@dataclass
class LessonsLearnedInput:
    incident_text: str = ""
    equipment_tag: str = ""
    incident_id: str = ""
    analysis_scope: str = "single"
    run_id: str = ""


# ── Collection Mapping ────────────────────────────────────────────────────────

DOC_TYPE_TO_COLLECTION = {
    "oem_manual": "10-oem-manuals",
    "compliance_regulation": "11-compliance-regs",
    "sop": "12-sops",
    "maintenance_log": "13-maintenance-logs",
    "inspection_report": "14-inspection-records",
    "incident_report": "15-incident-reports",
    # Fallbacks
    "work_order": "13-maintenance-logs",
    "pid": "10-oem-manuals",
    "unknown": "10-oem-manuals",
}


# ── Document Ingestion Workflow ───────────────────────────────────────────────

@workflow.defn
class DocumentIngestionWorkflow:
    """
    Complete document ingestion pipeline:
    1. OCR/Extract → raw text
    2. Doc Intelligence Agent → entities, relationships, chunks
    3. Embed chunks → pgvector
    4. KG Agent → update Neo4j graph

    Triggered by file upload API endpoint.
    """

    @workflow.run
    async def run(self, input: DocumentIngestionInput) -> dict:
        workflow.logger.info(f"Starting document ingestion: {input.file_name}")

        # Step 1: OCR / Text Extraction
        extract_result = await workflow.execute_activity(
            ocr_extract_activity,
            args=[input.file_path, input.file_name],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        raw_text = extract_result.get("raw_text", "")
        if not raw_text:
            return {
                "status": "failed",
                "error": extract_result.get("error", "No text extracted"),
                "file_name": input.file_name,
            }

        # Step 2: Document Intelligence Agent → entities + chunks
        doc_result = await workflow.execute_activity(
            doc_intelligence_activity,
            args=[raw_text, input.file_name, input.run_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Determine collection from detected doc_type
        detected_type = doc_result.get("doc_type", input.doc_type)
        collection = input.collection or DOC_TYPE_TO_COLLECTION.get(detected_type, "10-oem-manuals")

        # Step 3: Embed and store in pgvector
        embed_result = await workflow.execute_activity(
            embed_and_store_activity,
            args=[raw_text, input.file_path, collection, input.file_name],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Step 4: Update Knowledge Graph via KG Agent
        entities = doc_result.get("entities", [])
        relationships = doc_result.get("relationships", [])
        doc_metadata = doc_result.get("doc_metadata", {})

        graph_result = {}
        if entities or relationships:
            graph_result = await workflow.execute_activity(
                update_industrial_graph_activity,
                args=[entities, relationships, doc_metadata, input.run_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

        return {
            "status": "completed",
            "file_name": input.file_name,
            "doc_type": detected_type,
            "collection": collection,
            "pages_extracted": extract_result.get("pages", 0),
            "entities_found": len(entities),
            "relationships_found": len(relationships),
            "chunks_embedded": embed_result.get("chunks_ingested", 0),
            "graph_nodes_created": graph_result.get("nodes_created", 0),
            "graph_edges_created": graph_result.get("edges_created", 0),
            "summary": doc_result.get("summary", ""),
        }


# ── Maintenance Lifecycle Workflow ────────────────────────────────────────────

@workflow.defn
class MaintenanceLifecycleWorkflow:
    """
    Maintenance lifecycle pipeline:
    1. Record work order in graph + memory (if provided)
    2. Run Maintenance Agent (RCA + prediction)
    3. If high risk, flag for alert

    Triggered by CMMS work order creation or manual analysis request.
    """

    @workflow.run
    async def run(self, input: MaintenanceInput) -> dict:
        workflow.logger.info(f"Starting maintenance lifecycle for {input.equipment_tag}")

        # Step 1: Record work order (if provided)
        wo_result = {}
        if input.work_order_data:
            wo_result = await workflow.execute_activity(
                record_work_order_activity,
                args=[input.work_order_data],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

        # Step 2: Run Maintenance Agent
        maintenance_result = await workflow.execute_activity(
            maintenance_analysis_activity,
            args=[input.equipment_tag, input.analysis_type, input.incident_context, input.run_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Step 3: Check risk level — flag for alert if critical/high
        risk_level = maintenance_result.get("risk_level", "medium")
        requires_alert = risk_level in ("high", "critical")

        return {
            "status": "completed",
            "equipment_tag": input.equipment_tag,
            "work_order_recorded": bool(wo_result),
            "risk_level": risk_level,
            "requires_alert": requires_alert,
            "predictions_count": len(maintenance_result.get("predictions", [])),
            "recommendations_count": len(maintenance_result.get("recommendations", [])),
            "rca_root_cause": maintenance_result.get("rca", {}).get("root_cause", "N/A"),
            "analysis": maintenance_result,
        }


# ── Lessons Learned Workflow ──────────────────────────────────────────────────

@workflow.defn
class LessonsLearnedWorkflow:
    """
    Lessons learned pipeline:
    1. Run Lessons Learned Agent on incident(s)
    2. Lessons are auto-persisted to Reflection Memory by the agent
    3. Return warnings and patterns for proactive alerting

    Can be triggered per-incident or on a nightly schedule for cross-asset analysis.
    """

    @workflow.run
    async def run(self, input: LessonsLearnedInput) -> dict:
        workflow.logger.info(
            f"Starting lessons learned analysis: scope={input.analysis_scope}, "
            f"equipment={input.equipment_tag or 'all'}"
        )

        result = await workflow.execute_activity(
            lessons_learned_activity,
            args=[
                input.incident_text,
                input.equipment_tag,
                input.incident_id,
                input.analysis_scope,
                input.run_id,
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        return {
            "status": "completed",
            "lessons_extracted": len(result.get("lessons", [])),
            "warnings_generated": len(result.get("warnings", [])),
            "patterns_detected": len(result.get("patterns", [])),
            "analysis": result,
        }
