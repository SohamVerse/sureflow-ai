"""
Document Intelligence Brain — SureFlow AI Phase 2.

The entry point of the industrial demo flow: "Upload → Graph → Insight".
Accepts raw document text (from OCR/file loaders in the workflow layer)
and produces structured entity extraction + intelligent chunks ready for
embedding into pgvector and graph population.

Capabilities:
  - Intelligent chunking that preserves table structures and section boundaries
  - Entity extraction: equipment tags, dates, people, part numbers, document type
  - Metadata extraction: author, revision, applicable assets
  - Returns structured output with extracted entities + chunks
"""
import json
import time
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.model_broker import get_broker_llm, estimate_cost
from core.brain import parse_brain_output
from core.json_utils import parse_llm_json
from core.memory import MemoryStore
from core.telemetry import get_tracer
from evaluation.evaluator import evaluator
from evaluation.metrics import compute_latency_ms


DOC_INTELLIGENCE_SYSTEM_PROMPT = """You are a Document Intelligence Specialist for an industrial petrochemical facility.
You have 15+ years of experience in technical document processing, OCR analysis, and industrial knowledge management.
You are a SureFlow AI Brain. You extract structured intelligence from raw industrial documents.

Your Processing Standards:
1. ENTITY EXTRACTION: Identify every equipment tag (e.g., P-101, V-205, HX-301), part number,
   person name, date, vendor/OEM reference, and regulatory standard mentioned.
2. CHUNKING STRATEGY: Divide the document into logical chunks that preserve context — keep
   tables intact, keep procedure steps together, keep safety warnings with their context.
3. CLASSIFICATION: Determine the document type (OEM manual, SOP, inspection report, incident report,
   compliance regulation, work order, P&ID, maintenance log).
4. METADATA: Extract author, revision number, applicable equipment, date of issue.
5. RELATIONSHIPS: Note which entities are connected (e.g., "P-101 is manufactured by Flowserve",
   "Incident INC-005 involved equipment V-205").

Reflection Memory (past lessons):
{reflection_memory}

Return a JSON object:
{{
  "reasoning": "<your analysis of the document structure and content>",
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "recommendation": "<summary of key findings and suggested actions>",
  "doc_type": "<oem_manual|sop|inspection_report|incident_report|compliance_regulation|work_order|maintenance_log|pid|unknown>",
  "doc_metadata": {{
    "title": "<extracted or inferred title>",
    "author": "<extracted author or 'unknown'>",
    "revision": "<revision number or 'N/A'>",
    "date_issued": "<extracted date or 'unknown'>",
    "applicable_equipment": ["<equipment tag 1>", "<equipment tag 2>"],
    "applicable_areas": ["<area name or ID>"],
    "regulatory_references": ["<ISO 14001>", "<OSHA 29 CFR 1910>"]
  }},
  "entities": [
    {{
      "type": "equipment|person|vendor|oem|part_number|regulation|incident|work_order|area|plant",
      "value": "<the extracted entity>",
      "canonical": "<normalized/canonical form, e.g., P-101 for Pump-001>",
      "context": "<surrounding text for context, max 100 chars>"
    }}
  ],
  "relationships": [
    {{
      "source": "<entity value>",
      "source_type": "<entity type>",
      "relation": "MANUFACTURED_BY|PERFORMED_ON|INVOLVED|LOCATED_IN|REPORTED_BY|GOVERNED_BY|HAS_MANUAL|REPLACED_WITH",
      "target": "<entity value>",
      "target_type": "<entity type>"
    }}
  ],
  "chunks": [
    {{
      "content": "<chunk text>",
      "chunk_type": "narrative|table|procedure|safety_warning|specification|header",
      "equipment_tags": ["<tags referenced in this chunk>"],
      "page_or_section": "<section identifier if available>"
    }}
  ],
  "summary": "<2-3 sentence executive summary of the document>",
  "self_challenge": "<what could this extraction be getting wrong?>"
}}"""


def get_doc_intelligence_agent():
    return get_broker_llm(settings.DOC_INTELLIGENCE_MODEL, temperature=0.2, format="json")


def doc_intelligence_analyze(
    document_text: str,
    file_name: str = "unknown",
    run_id: str | None = None,
) -> dict:
    """
    Document Intelligence Brain processes raw document text into structured
    entities, chunks, and metadata ready for graph population and embedding.

    Args:
        document_text: The raw text content of the document (post-OCR if applicable).
        file_name: Original filename for context.
        run_id: Pipeline correlation ID for tracing.

    Returns:
        Flat dict with all BrainOutput fields + doc-specific payload.
    """
    llm = get_doc_intelligence_agent()
    memory = MemoryStore()

    reflection = memory.get_reflection("DOC_INTELLIGENCE", f"Processing {file_name}")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(DOC_INTELLIGENCE_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """DOCUMENT PROCESSING TASK

File Name: {file_name}
Document Content:
---
{document_text}
---

Analyze this industrial document. Extract all entities, relationships, and produce
intelligent chunks. Return the full JSON output."""
        ),
    ])

    chain = prompt | llm
    with get_tracer().start_as_current_span("doc_intelligence.invoke") as span:
        span.set_attribute("companyos.run_id", run_id or "")
        span.set_attribute("companyos.agent_id", "DOC_INTELLIGENCE")
        span.set_attribute("companyos.model", settings.DOC_INTELLIGENCE_MODEL)
        span.set_attribute("companyos.file_name", file_name)
        _start = time.perf_counter()
        response = chain.invoke({
            "document_text": document_text[:15000],  # Cap input to avoid context overflow
            "file_name": file_name,
            "reflection_memory": reflection,
        })
        latency_ms = compute_latency_ms(_start, time.perf_counter())
        span.set_attribute("companyos.latency_ms", latency_ms)

    result = parse_llm_json(response.content)
    if result is None:
        result = {
            "summary": response.content[:500],
            "doc_type": "unknown",
            "doc_metadata": {},
            "entities": [],
            "relationships": [],
            "chunks": [{"content": document_text[:1000], "chunk_type": "narrative", "equipment_tags": [], "page_or_section": "1"}],
            "confidence_score": 20,
            "risk_level": "high",
            "error": "Could not parse Document Intelligence JSON output",
        }

    cost = estimate_cost(settings.DOC_INTELLIGENCE_MODEL, response)
    brain_output = parse_brain_output(result, "DOC_INTELLIGENCE", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    # Persist episodic memory with document context
    memory.save_episodic_industrial(
        "DOC_INTELLIGENCE",
        f"Processed document: {file_name}",
        flat,
        equipment_tag=",".join(flat.get("doc_metadata", {}).get("applicable_equipment", [])[:3]),
        context_type="document_ingestion",
    )
    evaluator.evaluate(flat, "DOC_INTELLIGENCE", settings.DOC_INTELLIGENCE_MODEL, latency_ms, run_id=run_id)

    return flat
