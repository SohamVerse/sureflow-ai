"""
Compliance Brain — SureFlow OS Phase 2.

Ensures operations meet regulatory standards (ISO, OSHA, PESO, Factory Act).
Cross-references inspection records with regulatory requirements, identifies
compliance gaps, checks SOP adherence, and generates audit evidence summaries.

Capabilities:
  - Cross-reference inspections with regulatory requirements
  - Identify compliance gaps (equipment with incidents but no recent inspections)
  - Check SOP adherence against regulatory checklists
  - Generate audit evidence packs and readiness assessments
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


COMPLIANCE_SYSTEM_PROMPT = """You are a Senior Compliance & Regulatory Specialist for an industrial petrochemical facility.
You have 15+ years of experience in OSHA, ISO 14001, ISO 45001, PESO (Petroleum and Explosives Safety Organisation),
and Indian Factories Act compliance. You are a SureFlow OS Brain.

Your Responsibilities:
1. GAP ANALYSIS: Cross-reference inspection records with regulatory requirements.
   If OSHA 29 CFR 1910.119 requires annual PSV inspections and the last inspection was
   18 months ago, flag it as a critical gap.
2. SOP COMPLIANCE: Verify that Standard Operating Procedures cover all regulatory requirements.
   Missing SOPs for hazardous operations are high-severity findings.
3. AUDIT READINESS: Assess whether the facility is audit-ready. Compile evidence summaries.
4. RISK PRIORITIZATION: Rank compliance gaps by severity — safety-critical gaps first.
5. DOCUMENTATION: Note where documentation is missing, expired, or insufficient.

Compliance Regulations:
{compliance_regs}

Standard Operating Procedures:
{sop_data}

Inspection Records:
{inspection_data}

Knowledge Graph Context:
{graph_context}

Compliance Gaps from Graph (equipment with incidents but missing inspections):
{graph_compliance_gaps}

Incident History:
{incident_data}

Lessons Learned:
{lessons_learned}

Reflection Memory:
{reflection_memory}

Return a JSON object:
{{
  "reasoning": "<your analysis of the compliance posture>",
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high|critical",
  "recommendation": "<primary compliance recommendation>",
  "overall_compliance_status": "compliant|partially_compliant|non_compliant|unknown",
  "compliance_score": <0-100>,
  "gaps": [
    {{
      "gap_id": "<unique identifier, e.g., GAP-001>",
      "equipment_tag": "<affected equipment, if applicable>",
      "area": "<affected area, if applicable>",
      "regulation": "<regulatory standard, e.g., OSHA 29 CFR 1910.119>",
      "requirement": "<what the regulation requires>",
      "current_state": "<what exists now (or doesn't)>",
      "finding": "<concise description of the gap>",
      "severity": "critical|major|minor|observation",
      "due_date": "<when this must be resolved, if regulation specifies>",
      "evidence_available": true,
      "remediation": "<specific steps to close this gap>"
    }}
  ],
  "audit_readiness": {{
    "overall_status": "ready|needs_work|not_ready",
    "areas_reviewed": <count>,
    "findings_count": {{
      "critical": <count>,
      "major": <count>,
      "minor": <count>,
      "observations": <count>
    }},
    "evidence_summary": "<what documentation exists and what's missing>",
    "estimated_remediation_days": <number>
  }},
  "sop_gaps": [
    {{
      "sop_title": "<SOP name or 'MISSING'>",
      "regulatory_requirement": "<what regulation requires it>",
      "status": "adequate|needs_update|missing|expired",
      "finding": "<what needs to change>"
    }}
  ],
  "recommendations": [
    {{
      "action": "<specific compliance action>",
      "priority": "immediate|within_30_days|within_90_days|annual_review",
      "regulation": "<regulatory driver>",
      "responsible_party": "<who should action this>",
      "deadline": "<regulatory deadline if applicable>"
    }}
  ],
  "regulatory_landscape": {{
    "applicable_regulations": ["<reg1>", "<reg2>"],
    "upcoming_changes": ["<any regulatory changes on the horizon>"],
    "industry_trends": ["<compliance trends relevant to this facility>"]
  }},
  "self_challenge": "<what compliance risks might we be underestimating?>"
}}"""


def get_compliance_agent():
    return get_broker_llm(settings.COMPLIANCE_MODEL, temperature=0.2, format="json")


def compliance_analyze(
    scope: str = "facility",
    area_id: str = "",
    equipment_tag: str = "",
    regulation_focus: str = "",
    run_id: str | None = None,
    plant_id: str | None = None,
) -> dict:
    """
    Compliance Brain performs regulatory gap analysis and audit readiness assessment.

    Args:
        scope: "facility" (whole plant), "area" (specific area), or "equipment" (single asset).
        area_id: Area to focus on (if scope is "area").
        equipment_tag: Equipment to focus on (if scope is "equipment").
        regulation_focus: Optional specific regulation to check against.
        run_id: Pipeline correlation ID.

    Returns:
        Flat dict with BrainOutput fields + compliance-specific payload.
    """
    llm = get_compliance_agent()
    memory = MemoryStore()

    # ── Gather context ──────────────────────────────────────────────────────
    reflection = memory.get_reflection("COMPLIANCE", f"Compliance review ({scope})")

    # Graph data (plant-scoped)
    graph_context = industrial_graph.get_industrial_overview(plant_id=plant_id)
    graph_compliance_gaps = []
    if area_id:
        graph_compliance_gaps = industrial_graph.get_compliance_gaps(area_id)
    elif scope == "facility":
        # Check all areas — get plant hierarchy for area IDs
        hierarchy = industrial_graph.get_plant_hierarchy(plant_id=plant_id)
        for plant in hierarchy:
            for area in plant.get("children", []):
                aid = area.get("id", "")
                if aid:
                    area_gaps = industrial_graph.get_compliance_gaps(aid)
                    graph_compliance_gaps.extend(area_gaps)

    # Semantic memory (plant-scoped)
    compliance_regs = memory.get_compliance_regs(regulation_focus or "regulatory compliance requirements", plant_id=plant_id)
    sop_data = memory.get_sops("standard operating procedure compliance", plant_id=plant_id)
    incident_data = memory.get_incident_reports("compliance safety incident", plant_id=plant_id)
    inspection_query = equipment_tag or area_id or "inspection audit compliance"
    inspection_data = memory.query_semantic("14-inspection-records", inspection_query, n_results=5, plant_id=plant_id)
    lessons_learned = memory.get_all_operational_lessons(limit=5, plant_id=plant_id)

    task_description = f"Compliance analysis ({scope})"
    if area_id:
        task_description += f" for area {area_id}"
    if equipment_tag:
        task_description += f" for {equipment_tag}"

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(COMPLIANCE_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """COMPLIANCE ANALYSIS TASK

Scope: {scope}
Area: {area_id}
Equipment: {equipment_tag}
Regulation Focus: {regulation_focus}

Perform a thorough compliance gap analysis. Cross-reference inspection records
with regulatory requirements. Assess audit readiness. Return the full JSON output."""
        ),
    ])

    chain = prompt | llm
    with get_tracer().start_as_current_span("compliance.invoke") as span:
        span.set_attribute("companyos.run_id", run_id or "")
        span.set_attribute("companyos.agent_id", "COMPLIANCE")
        span.set_attribute("companyos.model", settings.COMPLIANCE_MODEL)
        _start = time.perf_counter()
        response = chain.invoke({
            "scope": scope,
            "area_id": area_id or "All areas",
            "equipment_tag": equipment_tag or "All equipment",
            "regulation_focus": regulation_focus or "All applicable regulations (OSHA, ISO, PESO, Factories Act)",
            "compliance_regs": compliance_regs,
            "sop_data": sop_data,
            "inspection_data": json.dumps([r.get("content", "") for r in inspection_data] if inspection_data else []),
            "graph_context": graph_context,
            "graph_compliance_gaps": json.dumps(graph_compliance_gaps[:10]),
            "incident_data": incident_data,
            "lessons_learned": lessons_learned,
            "reflection_memory": reflection,
        })
        latency_ms = compute_latency_ms(_start, time.perf_counter())
        span.set_attribute("companyos.latency_ms", latency_ms)

    result = parse_llm_json(response.content)
    if result is None:
        import logging
        logging.getLogger("companyos.compliance").error(
            f"Failed to parse Compliance Agent JSON even after repair. Raw content: {response.content}"
        )
        result = {
            "overall_compliance_status": "unknown",
            "compliance_score": 0,
            "gaps": [],
            "audit_readiness": {"overall_status": "not_ready", "findings_count": {}},
            "sop_gaps": [],
            "recommendations": [],
            "confidence_score": 15,
            "risk_level": "high",
            "error": f"Could not parse Compliance Agent JSON output. Content snippet: {str(response.content)[:200]}",
        }

    cost = estimate_cost(settings.COMPLIANCE_MODEL, response)
    brain_output = parse_brain_output(result, "COMPLIANCE", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic_industrial(
        "COMPLIANCE", task_description, flat,
        equipment_tag=equipment_tag,
        context_type="compliance_audit",
        plant_id=plant_id or "",
    )
    evaluator.evaluate(flat, "COMPLIANCE", settings.COMPLIANCE_MODEL, latency_ms, run_id=run_id)

    return flat
