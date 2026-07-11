"""
Lessons Learned Brain — SureFlow OS Phase 2.

Powers the "learned from P-101 failure, warns about P-102" demo moment.
Parses incidents and near-misses, extracts lessons, writes to Reflection Memory
with equipment tags, and cross-references similar equipment to proactively
inject warnings into other agents' contexts.

Capabilities:
  - Parse incidents/near-misses → extract actionable lessons
  - Write to Reflection Memory with equipment and incident context
  - Cross-reference similar equipment for proactive warnings
  - Detect recurring failure patterns across assets/vendors
"""
import json
import time
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.model_broker import get_broker_llm, estimate_cost
from core.brain import parse_brain_output
from core.memory import MemoryStore
from core.telemetry import get_tracer
from evaluation.evaluator import evaluator
from evaluation.metrics import compute_latency_ms
from knowledge_graph.industrial_store import industrial_graph


LESSONS_LEARNED_SYSTEM_PROMPT = """You are an Organizational Learning Specialist for an industrial petrochemical facility.
You have 15+ years of experience in incident investigation, CAPA (Corrective and Preventive Actions),
and organizational knowledge management. You transform failures into institutional wisdom.

Your Responsibilities:
1. LESSON EXTRACTION: From every incident, near-miss, or failure report, extract the
   actionable lesson — not a platitude, but a specific, implementable takeaway.
2. CROSS-ASSET WARNING: If Pump P-101 failed due to bearing wear at 4000 hours,
   proactively warn about Pump P-102 (same class/OEM) approaching similar runtime.
3. PATTERN DETECTION: Identify recurring failures across assets, vendors, or procedures.
   "This is the 3rd seal failure on Flowserve pumps in 6 months" is a pattern.
4. SEVERITY CLASSIFICATION: Classify lessons by severity — safety incidents get highest priority.
5. ROOT CAUSE TAGGING: Tag each lesson to its root cause category:
   human_error, equipment_failure, design_flaw, procedure_gap, vendor_quality, environmental.

Knowledge Graph Context (equipment and relationships):
{graph_context}

Equipment Context:
{equipment_context}

Existing Lessons Learned:
{existing_lessons}

Incident Reports:
{incident_data}

All Equipment (for cross-asset matching):
{all_equipment}

All Incidents:
{all_incidents}

Reflection Memory:
{reflection_memory}

Return a JSON object:
{{
  "reasoning": "<your analysis of the incidents and lessons extracted>",
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high|critical",
  "recommendation": "<primary recommendation based on lessons>",
  "lessons": [
    {{
      "lesson": "<specific, actionable lesson>",
      "equipment_tag": "<primary equipment involved>",
      "incident_id": "<related incident ID if applicable>",
      "category": "operational_failure|safety_incident|near_miss|design_flaw|procedure_gap|vendor_quality",
      "severity": "critical|high|medium|low",
      "root_cause": "human_error|equipment_failure|design_flaw|procedure_gap|vendor_quality|environmental",
      "corrective_action": "<specific action to prevent recurrence>",
      "preventive_action": "<broader action to prevent similar issues>"
    }}
  ],
  "warnings": [
    {{
      "target_equipment": "<equipment tag at risk>",
      "risk_description": "<what could happen>",
      "risk_level": "critical|high|medium|low",
      "reason": "<why this equipment is at risk — based on which lesson>",
      "based_on_incident": "<incident ID that inspired this warning>",
      "recommended_action": "<what to do proactively>"
    }}
  ],
  "patterns": [
    {{
      "pattern": "<description of the recurring pattern>",
      "frequency": "<how often — e.g., '3 times in 6 months'>",
      "affected_assets": ["<tag1>", "<tag2>"],
      "affected_vendors": ["<vendor1>"],
      "trend": "increasing|stable|decreasing",
      "systemic_recommendation": "<what to change at the system level>"
    }}
  ],
  "self_challenge": "<what might we be missing or over-interpreting?>"
}}"""


def get_lessons_learned_agent():
    return get_broker_llm(settings.LESSONS_LEARNED_MODEL, temperature=0.2, format="json")


def lessons_learned_analyze(
    incident_text: str = "",
    equipment_tag: str = "",
    incident_id: str = "",
    analysis_scope: str = "single",
    run_id: str | None = None,
) -> dict:
    """
    Lessons Learned Brain analyzes incidents and extracts actionable lessons.

    Args:
        incident_text: Description of the incident or near-miss to analyze.
        equipment_tag: Primary equipment involved (optional).
        incident_id: Incident ID for tracing (optional).
        analysis_scope: "single" (one incident) or "cross_asset" (pattern analysis across all).
        run_id: Pipeline correlation ID.

    Returns:
        Flat dict with BrainOutput fields + lessons/warnings/patterns payload.
    """
    llm = get_lessons_learned_agent()
    memory = MemoryStore()

    # ── Gather context ──────────────────────────────────────────────────────
    reflection = memory.get_reflection("LESSONS_LEARNED", f"Lessons analysis for {equipment_tag or 'general'}")
    existing_lessons = memory.get_all_operational_lessons(limit=10)

    # Graph data
    graph_context = industrial_graph.get_industrial_overview()
    equipment_context = ""
    if equipment_tag:
        equipment_context = industrial_graph.get_equipment_context(equipment_tag)

    all_equipment = industrial_graph.get_all_equipment()
    all_incidents = industrial_graph.get_all_incidents(limit=20)

    # Semantic data
    incident_data = memory.get_incident_reports(incident_text or equipment_tag or "incident failure analysis")

    task_description = f"Lessons learned analysis ({analysis_scope})"
    if equipment_tag:
        task_description += f" for {equipment_tag}"
    if incident_id:
        task_description += f" — Incident {incident_id}"

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(LESSONS_LEARNED_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """LESSONS LEARNED ANALYSIS TASK

Scope: {analysis_scope}
Equipment: {equipment_tag}
Incident ID: {incident_id}

Incident/Event Description:
{incident_text}

Extract actionable lessons, identify cross-asset warnings, and detect patterns.
For cross_asset scope, analyze all incidents and equipment for systemic patterns.
Return the full JSON output."""
        ),
    ])

    chain = prompt | llm
    with get_tracer().start_as_current_span("lessons_learned.invoke") as span:
        span.set_attribute("companyos.run_id", run_id or "")
        span.set_attribute("companyos.agent_id", "LESSONS_LEARNED")
        span.set_attribute("companyos.model", settings.LESSONS_LEARNED_MODEL)
        span.set_attribute("companyos.equipment_tag", equipment_tag)
        _start = time.perf_counter()
        response = chain.invoke({
            "incident_text": incident_text or "No specific incident — perform cross-asset pattern analysis.",
            "equipment_tag": equipment_tag or "N/A",
            "incident_id": incident_id or "N/A",
            "analysis_scope": analysis_scope,
            "graph_context": graph_context,
            "equipment_context": equipment_context or "No specific equipment context.",
            "existing_lessons": existing_lessons,
            "incident_data": incident_data,
            "all_equipment": json.dumps(all_equipment[:15]),
            "all_incidents": json.dumps(all_incidents[:15]),
            "reflection_memory": reflection,
        })
        latency_ms = compute_latency_ms(_start, time.perf_counter())
        span.set_attribute("companyos.latency_ms", latency_ms)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        try:
            result = json.loads(content)
        except Exception:
            result = {
                "lessons": [],
                "warnings": [],
                "patterns": [],
                "confidence_score": 20,
                "risk_level": "medium",
                "error": "Could not parse Lessons Learned JSON output",
            }

    # Persist lessons to Reflection Memory
    _persist_lessons(memory, result, equipment_tag, incident_id)

    cost = estimate_cost(settings.LESSONS_LEARNED_MODEL, response)
    brain_output = parse_brain_output(result, "LESSONS_LEARNED", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic_industrial(
        "LESSONS_LEARNED", task_description, flat,
        equipment_tag=equipment_tag,
        context_type="lessons_analysis",
    )
    evaluator.evaluate(flat, "LESSONS_LEARNED", settings.LESSONS_LEARNED_MODEL, latency_ms, run_id=run_id)

    return flat


def _persist_lessons(memory: MemoryStore, result: dict, equipment_tag: str, incident_id: str) -> None:
    """
    Write extracted lessons to Reflection Memory so they're automatically
    injected into future agent prompts for the same equipment.
    """
    for lesson in result.get("lessons", []):
        try:
            memory.save_reflection_industrial(
                agent_id="LESSONS_LEARNED",
                task=lesson.get("corrective_action", "Lesson from incident analysis"),
                failure_reason=lesson.get("lesson", ""),
                lesson=lesson.get("preventive_action", lesson.get("lesson", "")),
                equipment_tag=lesson.get("equipment_tag", equipment_tag),
                incident_id=lesson.get("incident_id", incident_id),
                category=lesson.get("category", "operational_failure"),
                source="incident_report",
            )
        except Exception:
            continue  # Graceful degradation — don't crash if memory write fails
