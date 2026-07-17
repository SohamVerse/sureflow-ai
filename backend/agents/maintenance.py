"""
Maintenance Intelligence Brain — SureFlow OS Phase 2.

The reliability engineering expert. Analyzes equipment history for failure
patterns, performs Root Cause Analysis (RCA), predicts likely failures, and
recommends preventive maintenance actions.

Core differentiator for the "proactive intelligence" narrative.

Capabilities:
  - Failure pattern analysis across similar assets
  - Root Cause Analysis using historical incidents + work orders
  - Failure prediction based on similar asset history
  - Preventive maintenance recommendations
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


MAINTENANCE_SYSTEM_PROMPT = """You are a Senior Reliability Engineer with 20+ years of experience in petrochemical plants.
You specialize in Root Cause Analysis (RCA), failure prediction, and preventive maintenance strategy.
You are a SureFlow OS Brain. You provide proactive maintenance intelligence.

Your Analytical Framework:
1. ROOT CAUSE ANALYSIS: Use the 5-Why method and Ishikawa (fishbone) diagram thinking.
   Don't stop at symptoms — dig to the root cause.
2. PATTERN RECOGNITION: Look for failure patterns across similar assets. If P-101 failed
   due to bearing wear at 4500 hours, P-102 (same class) is likely at similar risk.
3. FAILURE PREDICTION: Based on historical data, predict which equipment is most likely
   to fail next and when. Consider MTBF (Mean Time Between Failures).
4. COST-BENEFIT: Every recommendation should weigh the cost of action vs. cost of failure.
5. SAFETY-FIRST: If a failure mode has safety implications, escalate immediately.

Equipment Context (Knowledge Graph):
{equipment_context}

Asset Timeline (incidents, work orders, inspections):
{asset_timeline}

OEM Specifications:
{oem_specs}

Maintenance Logs:
{maintenance_logs}

Lessons Learned:
{lessons_learned}

Reflection Memory:
{reflection_memory}

Episodic Memory (past maintenance analyses):
{episodic_memory}

All Equipment in System (for cross-asset pattern matching):
{all_equipment}

Return a JSON object:
{{
  "reasoning": "<full RCA thought process — 5-Why chain, contributing factors>",
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high|critical",
  "recommendation": "<primary maintenance recommendation>",
  "rca": {{
    "root_cause": "<identified root cause>",
    "contributing_factors": ["<factor 1>", "<factor 2>"],
    "evidence": ["<evidence point 1 with source>", "<evidence point 2>"],
    "five_why_chain": [
      "<Why 1: immediate cause>",
      "<Why 2: underlying cause>",
      "<Why 3: systemic cause>",
      "<Why 4: organizational cause>",
      "<Why 5: root cause>"
    ],
    "failure_mode": "<the specific failure mode, e.g., bearing fatigue, seal erosion>"
  }},
  "predictions": [
    {{
      "equipment_tag": "<tag>",
      "equipment_name": "<name>",
      "failure_mode": "<predicted failure>",
      "probability": <0-100>,
      "timeframe": "<within 30 days|within 90 days|within 6 months|within 12 months>",
      "basis": "<why this prediction — similar asset data, MTBF, age, usage>"
    }}
  ],
  "recommendations": [
    {{
      "action": "<specific maintenance action>",
      "priority": "critical|high|medium|low",
      "equipment_tag": "<tag>",
      "justification": "<why this action, cost-benefit>",
      "estimated_cost": "<rough cost estimate>",
      "estimated_downtime": "<hours/days>",
      "failure_cost_if_ignored": "<estimated cost of inaction>"
    }}
  ],
  "similar_asset_analysis": {{
    "assets_compared": ["<tag1>", "<tag2>"],
    "common_failure_modes": ["<mode1>"],
    "mtbf_estimate_hours": <estimated hours>,
    "pattern_summary": "<what the cross-asset comparison reveals>"
  }},
  "self_challenge": "<what could this analysis be missing?>"
}}"""


def get_maintenance_agent():
    return get_broker_llm(settings.MAINTENANCE_MODEL, temperature=0.3, format="json")


def maintenance_analyze(
    equipment_tag: str,
    analysis_type: str = "full",
    incident_context: str = "",
    run_id: str | None = None,
    plant_id: str | None = None,
) -> dict:
    """
    Maintenance Intelligence Brain performs RCA and failure prediction.

    Args:
        equipment_tag: The primary equipment to analyze (e.g., "P-101").
        analysis_type: "rca" (root cause only), "prediction" (failure forecast), or "full" (both).
        incident_context: Optional incident description for targeted RCA.
        run_id: Pipeline correlation ID.

    Returns:
        Flat dict with BrainOutput fields + maintenance-specific payload.
    """
    llm = get_maintenance_agent()
    memory = MemoryStore()

    # ── Gather industrial context (plant-scoped) ───────────────────────────
    reflection = memory.get_reflection("MAINTENANCE", f"Maintenance analysis for {equipment_tag}")
    episodic = memory.get_episodic_by_equipment(equipment_tag, limit=5, plant_id=plant_id)

    # Graph data
    equipment_context = industrial_graph.get_equipment_context(equipment_tag)
    asset_timeline = industrial_graph.get_asset_timeline(equipment_tag, limit=15)
    all_equipment = industrial_graph.get_all_equipment(plant_id=plant_id)

    # Semantic memory
    oem_specs = memory.get_oem_manual(f"maintenance specifications {equipment_tag}", plant_id=plant_id)
    maintenance_logs = memory.get_maintenance_logs(f"maintenance history {equipment_tag}", plant_id=plant_id)
    lessons_learned = memory.get_lessons_by_equipment(equipment_tag, limit=5, plant_id=plant_id)

    task_description = f"Maintenance analysis ({analysis_type}) for {equipment_tag}"
    if incident_context:
        task_description += f" — Incident: {incident_context[:100]}"

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(MAINTENANCE_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """MAINTENANCE ANALYSIS TASK

Equipment: {equipment_tag}
Analysis Type: {analysis_type}
Incident Context: {incident_context}

Perform a thorough {analysis_type} analysis for this equipment. Use all available
data sources. If performing RCA, identify the root cause. If predicting failures,
assess similar assets too. Return the full JSON output."""
        ),
    ])

    chain = prompt | llm
    with get_tracer().start_as_current_span("maintenance.invoke") as span:
        span.set_attribute("companyos.run_id", run_id or "")
        span.set_attribute("companyos.agent_id", "MAINTENANCE")
        span.set_attribute("companyos.model", settings.MAINTENANCE_MODEL)
        span.set_attribute("companyos.equipment_tag", equipment_tag)
        _start = time.perf_counter()
        response = chain.invoke({
            "equipment_tag": equipment_tag,
            "analysis_type": analysis_type,
            "incident_context": incident_context or "No specific incident — general health assessment.",
            "equipment_context": equipment_context,
            "asset_timeline": json.dumps(asset_timeline[:10]),
            "oem_specs": oem_specs,
            "maintenance_logs": maintenance_logs,
            "lessons_learned": lessons_learned,
            "reflection_memory": reflection,
            "episodic_memory": json.dumps(episodic[:5]),
            "all_equipment": json.dumps(all_equipment[:20]),
        })
        latency_ms = compute_latency_ms(_start, time.perf_counter())
        span.set_attribute("companyos.latency_ms", latency_ms)

    result = parse_llm_json(response.content)
    if result is None:
        result = {
            "rca": {"root_cause": "Analysis failed", "contributing_factors": [], "evidence": [], "five_why_chain": [], "failure_mode": "unknown"},
            "predictions": [],
            "recommendations": [],
            "confidence_score": 15,
            "risk_level": "high",
            "error": "Could not parse Maintenance Agent JSON output",
        }

    cost = estimate_cost(settings.MAINTENANCE_MODEL, response)
    brain_output = parse_brain_output(result, "MAINTENANCE", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    # Persist to episodic memory, tagged to equipment + plant
    memory.save_episodic_industrial(
        "MAINTENANCE", task_description, flat,
        equipment_tag=equipment_tag,
        context_type="maintenance_analysis",
        plant_id=plant_id or "",
    )
    evaluator.evaluate(flat, "MAINTENANCE", settings.MAINTENANCE_MODEL, latency_ms, run_id=run_id)

    return flat
