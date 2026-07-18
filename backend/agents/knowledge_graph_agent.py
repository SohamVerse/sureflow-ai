"""
Knowledge Graph Brain — SureFlow AI Phase 2.

Takes extracted entities from the Document Intelligence Agent and writes/updates
relationships in the Industrial Knowledge Graph (Neo4j). Handles entity
deduplication, relationship type resolution, and graph evolution.

Capabilities:
  - Accept entity lists from Doc Intelligence output
  - Resolve/deduplicate entities (e.g., "Pump-001" = "P-001")
  - Determine relationship types between entities per the industrial ontology
  - Execute writes to IndustrialGraphStore
  - Return summary of nodes/edges created or updated
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
from knowledge_graph.industrial_store import industrial_graph


KG_AGENT_SYSTEM_PROMPT = """You are a Knowledge Graph Specialist for an industrial petrochemical facility.
You are an expert in industrial ontology, entity resolution, and graph database management.
You are a SureFlow AI Brain. You maintain the Industrial Knowledge Graph in Neo4j.

Your Responsibilities:
1. ENTITY RESOLUTION: Normalize entity names — "Pump-001", "P-001", and "Pump 001" are all the same
   asset. Use the shorter tag form (e.g., "P-001") as canonical. Equipment tags follow the pattern:
   P=Pump, V=Valve, HX=Heat Exchanger, CT=Cooling Tower, BLR=Boiler, TK=Tank, C=Compressor.
2. RELATIONSHIP MAPPING: Map extracted relationships to the industrial ontology:
   - Equipment → Area (LOCATED_IN)
   - Equipment → AssetClass (IS_TYPE)
   - Equipment → OEM (MANUFACTURED_BY)
   - Incident → Equipment (INVOLVED)
   - WorkOrder → Equipment (PERFORMED_ON)
   - Document → Equipment (HAS_MANUAL)
   - Inspection → Equipment (INSPECTED)
   - Area → Plant (CONTAINS)
3. DEDUPLICATION: Before creating new nodes, check existing graph context for matches.
4. CONFIDENCE: Rate your confidence in entity resolution — ambiguous matches get lower scores.

Existing Industrial Knowledge Graph:
{graph_context}

Reflection Memory (past lessons):
{reflection_memory}

You will receive a list of entities and relationships extracted from a document.
Resolve them, deduplicate, and produce graph operations.

Return a JSON object:
{{
  "reasoning": "<your analysis of the entities and how you resolved them>",
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "recommendation": "<summary of graph updates performed>",
  "entities_resolved": [
    {{
      "original": "<as extracted>",
      "canonical": "<normalized form>",
      "type": "equipment|area|plant|oem|vendor|incident|work_order|document|operator|engineer",
      "is_new": true,
      "resolution_confidence": <0-100>,
      "matched_existing": "<existing node ID if matched, else null>"
    }}
  ],
  "graph_operations": [
    {{
      "operation": "create_node|update_node|create_edge",
      "node_type": "<Plant|Area|Equipment|Incident|...>",
      "properties": {{}},
      "source": "<for edges>",
      "target": "<for edges>",
      "edge_type": "<CONTAINS|INVOLVED|MANUFACTURED_BY|...>"
    }}
  ],
  "nodes_created": <count>,
  "nodes_updated": <count>,
  "edges_created": <count>,
  "deduplication_summary": "<how many duplicates were caught and resolved>",
  "self_challenge": "<what entity resolutions might be wrong?>"
}}"""


def get_kg_agent():
    return get_broker_llm(settings.KG_AGENT_MODEL, temperature=0.1, format="json")


def kg_agent_process(
    entities: list[dict],
    relationships: list[dict],
    doc_metadata: dict | None = None,
    run_id: str | None = None,
) -> dict:
    """
    Knowledge Graph Brain processes extracted entities and relationships,
    resolves them, and writes to the Industrial Knowledge Graph.

    Args:
        entities: List of entity dicts from Doc Intelligence (type, value, canonical, context).
        relationships: List of relationship dicts (source, relation, target).
        doc_metadata: Document metadata for context.
        run_id: Pipeline correlation ID.

    Returns:
        Flat dict with BrainOutput fields + graph operation summary.
    """
    llm = get_kg_agent()
    memory = MemoryStore()

    reflection = memory.get_reflection("KG_AGENT", "Knowledge graph update")
    graph_context = industrial_graph.get_industrial_overview()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(KG_AGENT_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """KNOWLEDGE GRAPH UPDATE TASK

Document Metadata:
{doc_metadata}

Extracted Entities:
{entities}

Extracted Relationships:
{relationships}

Resolve these entities, deduplicate against the existing graph, and produce
the graph operations to execute. Return the full JSON output."""
        ),
    ])

    chain = prompt | llm
    with get_tracer().start_as_current_span("kg_agent.invoke") as span:
        span.set_attribute("companyos.run_id", run_id or "")
        span.set_attribute("companyos.agent_id", "KG_AGENT")
        span.set_attribute("companyos.model", settings.KG_AGENT_MODEL)
        _start = time.perf_counter()
        response = chain.invoke({
            "entities": json.dumps(entities, indent=2),
            "relationships": json.dumps(relationships, indent=2),
            "doc_metadata": json.dumps(doc_metadata or {}, indent=2),
            "graph_context": graph_context,
            "reflection_memory": reflection,
        })
        latency_ms = compute_latency_ms(_start, time.perf_counter())
        span.set_attribute("companyos.latency_ms", latency_ms)

    result = parse_llm_json(response.content)
    if result is None:
        result = {
            "entities_resolved": [],
            "graph_operations": [],
            "nodes_created": 0,
            "nodes_updated": 0,
            "edges_created": 0,
            "confidence_score": 20,
            "risk_level": "high",
            "error": "Could not parse Knowledge Graph Agent JSON output",
        }

    # Execute the graph operations based on LLM output
    _execute_graph_operations(result, doc_metadata)

    cost = estimate_cost(settings.KG_AGENT_MODEL, response)
    brain_output = parse_brain_output(result, "KG_AGENT", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("KG_AGENT", "Knowledge graph update from document", flat)
    evaluator.evaluate(flat, "KG_AGENT", settings.KG_AGENT_MODEL, latency_ms, run_id=run_id)

    return flat


def _execute_graph_operations(result: dict, doc_metadata: dict | None) -> None:
    """
    Execute the graph operations determined by the KG Agent.
    Uses IndustrialGraphStore methods for safe, idempotent writes.
    """
    operations = result.get("graph_operations", [])

    for op in operations:
        try:
            op_type = op.get("operation", "")
            node_type = op.get("node_type", "")
            props = op.get("properties", {})

            if op_type == "create_node" or op_type == "update_node":
                if node_type == "Plant":
                    industrial_graph.record_plant(
                        plant_id=props.get("plant_id", props.get("id", "")),
                        name=props.get("name", ""),
                        location=props.get("location", ""),
                    )
                elif node_type == "Area":
                    industrial_graph.record_area(
                        area_id=props.get("area_id", props.get("id", "")),
                        name=props.get("name", ""),
                        plant_id=props.get("plant_id", ""),
                    )
                elif node_type == "Equipment":
                    industrial_graph.record_equipment(
                        equipment_tag=props.get("tag", props.get("equipment_tag", "")),
                        name=props.get("name", ""),
                        area_id=props.get("area_id", ""),
                        asset_class=props.get("asset_class", ""),
                        oem=props.get("oem", ""),
                    )
                elif node_type == "Incident":
                    industrial_graph.record_incident(
                        incident_id=props.get("incident_id", props.get("id", "")),
                        title=props.get("title", ""),
                        description=props.get("description", ""),
                        equipment_tag=props.get("equipment_tag", ""),
                        severity=props.get("severity", "medium"),
                        reported_by=props.get("reported_by", ""),
                        date=props.get("date", ""),
                    )
                elif node_type == "Document":
                    industrial_graph.record_document(
                        doc_id=props.get("doc_id", props.get("id", "")),
                        title=props.get("title", ""),
                        doc_type=props.get("type", props.get("doc_type", "")),
                        equipment_tag=props.get("equipment_tag", ""),
                        area_id=props.get("area_id", ""),
                    )
                elif node_type == "WorkOrder":
                    industrial_graph.record_work_order(
                        wo_id=props.get("wo_id", props.get("id", "")),
                        title=props.get("title", ""),
                        description=props.get("description", ""),
                        equipment_tag=props.get("equipment_tag", ""),
                        wo_type=props.get("type", "corrective"),
                        assigned_to=props.get("assigned_to", ""),
                        status=props.get("status", "open"),
                        incident_id=props.get("incident_id"),
                    )
                elif node_type == "Inspection":
                    industrial_graph.record_inspection(
                        inspection_id=props.get("inspection_id", props.get("id", "")),
                        title=props.get("title", ""),
                        equipment_tag=props.get("equipment_tag", ""),
                        inspector=props.get("inspector", ""),
                        result=props.get("result", "pass"),
                        date=props.get("date", ""),
                    )
            # Edge operations are handled implicitly by the node creation methods
            # (e.g., record_equipment links to Area, record_incident links to Equipment)
        except Exception:
            # Graceful degradation — log but don't crash
            continue
