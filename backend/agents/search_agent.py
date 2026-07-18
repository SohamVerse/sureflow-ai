"""
Search Brain (Industrial Copilot) — SureFlow AI Phase 2.

The conversational interface — the main way users interact with the system.
Implements hybrid search: Cypher graph traversal + pgvector semantic search,
then synthesizes answers from multiple sources with citations.

Capabilities:
  - Intent detection (equipment lookup, maintenance query, compliance, general)
  - Hybrid search: graph (structured) + vector (unstructured)
  - Multi-source synthesis with citations
  - Follow-up question suggestions
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


SEARCH_SYSTEM_PROMPT = """You are the Industrial Copilot for a petrochemical facility.
You are the primary conversational interface for plant engineers, operators, and managers.
You answer questions by combining structured knowledge (Knowledge Graph) with unstructured
documents (OEM manuals, SOPs, incident reports) to provide comprehensive, cited answers.

{plant_context}

Your Standards:
1. ACCURACY: Every claim must be traceable to a source. Never fabricate data.
2. CITATIONS: Always cite your sources — e.g., [OEM Manual: Flowserve Mark III], [Incident INC-003].
3. CONTEXT-AWARE: Use the full industrial context — equipment history, past incidents,
   lessons learned, maintenance records — to enrich your answers.
4. ACTIONABLE: End with concrete recommendations or next steps when appropriate.
5. SAFETY-FIRST: If a question involves safety, always flag relevant lessons learned
   and past incidents proactively.

Knowledge Graph Context (structured data):
{graph_context}

Equipment Context (if equipment-specific query):
{equipment_context}

OEM Manual Data:
{oem_data}

Compliance Regulations:
{compliance_data}

Standard Operating Procedures:
{sop_data}

Maintenance Logs:
{maintenance_data}

Incident Reports:
{incident_data}

Lessons Learned:
{lessons_learned}

Reflection Memory:
{reflection_memory}

Past Conversations (Episodic Memory):
{episodic_memory}

Return a JSON object:
{{
  "reasoning": "<your internal thought process — how you combined sources>",
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "recommendation": "<primary recommendation or key takeaway>",
  "intent": "equipment_lookup|maintenance_query|compliance_check|incident_analysis|general_question|safety_concern",
  "answer": "<comprehensive markdown-formatted answer with inline citations like [Source: document name]>",
  "citations": [
    {{
      "source": "<document or data source name>",
      "collection": "<pgvector collection or 'knowledge_graph'>",
      "relevance": <0.0-1.0>,
      "excerpt": "<relevant excerpt, max 200 chars>"
    }}
  ],
  "sources_consulted": ["<list of collections/systems actually queried>"],
  "equipment_mentioned": ["<equipment tags referenced in the answer>"],
  "safety_alerts": ["<any safety-related warnings that should be highlighted>"],
  "follow_up_questions": [
    "<suggested follow-up question 1>",
    "<suggested follow-up question 2>",
    "<suggested follow-up question 3>"
  ],
  "self_challenge": "<what might this answer be missing?>"
}}"""


def get_search_agent():
    return get_broker_llm(settings.SEARCH_AGENT_MODEL, temperature=0.3, format="json")


def _detect_equipment_tags(query: str) -> list[str]:
    """
    Simple heuristic to detect equipment tags in a query.
    Matches common industrial tag patterns: P-101, V-205, HX-301, CT-001, etc.
    """
    import re
    pattern = r'\b([A-Z]{1,3}-\d{2,4})\b'
    return re.findall(pattern, query.upper())


def search_copilot_query(
    query: str,
    conversation_history: list[dict] | None = None,
    run_id: str | None = None,
    user_role: str = "cto",
    user_plant_id: str | None = None,
    target_plant_id: str | None = None,
) -> dict:
    """
    Industrial Copilot performs hybrid search and synthesizes an answer.

    Args:
        query: User's natural language question.
        conversation_history: Previous Q&A turns for context.
        run_id: Pipeline correlation ID.

    Returns:
        Flat dict with BrainOutput fields + copilot-specific payload.
    """
    llm = get_search_agent()
    memory = MemoryStore()

    # Detect equipment tags in the query for targeted retrieval
    equipment_tags = _detect_equipment_tags(query)

    # Determine plant_id context for RBAC
    effective_plant_id = None
    if user_role == "plant_manager" and user_plant_id:
        effective_plant_id = user_plant_id
    elif target_plant_id:
        effective_plant_id = target_plant_id

    plant_context = f"You are currently viewing data specifically for the {effective_plant_id} plant. Restrict your answers and insights to this facility." if effective_plant_id else "You have global access across all plants."

    # ── Gather context from all knowledge sources ──────────────────────────
    reflection = memory.get_reflection("SEARCH_AGENT", query)
    episodic = memory.get_episodic("SEARCH_AGENT", limit=3)

    # Graph context
    if effective_plant_id:
        hierarchy = industrial_graph.get_plant_hierarchy(plant_id=effective_plant_id)
        graph_context = f"Hierarchy for {effective_plant_id}:\n{json.dumps(hierarchy, indent=2)}"
    else:
        graph_context = industrial_graph.get_industrial_overview()
    equipment_context = ""
    if equipment_tags:
        equipment_contexts = []
        for tag in equipment_tags[:3]:  # Cap at 3 to avoid context overflow
            ctx = industrial_graph.get_equipment_context(tag)
            equipment_contexts.append(ctx)
            # Also get asset timeline
            timeline = industrial_graph.get_asset_timeline(tag, limit=5)
            if timeline:
                equipment_contexts.append(f"Timeline for {tag}: {json.dumps(timeline[:5])}")
        equipment_context = "\n\n".join(equipment_contexts)

    # Semantic memory (pgvector) — query all relevant collections
    oem_data = memory.get_oem_manual(query, plant_id=effective_plant_id)
    compliance_data = memory.get_compliance_regs(query, plant_id=effective_plant_id)
    sop_data = memory.get_sops(query, plant_id=effective_plant_id)
    maintenance_data = memory.get_maintenance_logs(query, plant_id=effective_plant_id)
    incident_data = memory.get_incident_reports(query, plant_id=effective_plant_id)

    # Lessons learned — both general and equipment-specific (plant-scoped)
    lessons = memory.get_all_operational_lessons(limit=5, plant_id=effective_plant_id)
    if equipment_tags:
        for tag in equipment_tags[:2]:
            tag_lessons = memory.get_lessons_by_equipment(tag, limit=3, plant_id=effective_plant_id)
            lessons += "\n" + tag_lessons

    # Episodic context for equipment
    equipment_episodes = ""
    if equipment_tags:
        for tag in equipment_tags[:2]:
            episodes = memory.get_episodic_by_equipment(tag, limit=3, plant_id=effective_plant_id)
            if episodes:
                equipment_episodes += f"\nRecent episodes for {tag}: {json.dumps(episodes)}"

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SEARCH_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """USER QUERY: {query}

Conversation History:
{conversation_history}

Equipment Episodes:
{equipment_episodes}

Answer this question using ALL available knowledge sources. Provide citations
for every claim. Return the full JSON output."""
        ),
    ])

    chain = prompt | llm
    with get_tracer().start_as_current_span("search_copilot.invoke") as span:
        span.set_attribute("companyos.run_id", run_id or "")
        span.set_attribute("companyos.agent_id", "SEARCH_AGENT")
        span.set_attribute("companyos.model", settings.SEARCH_AGENT_MODEL)
        span.set_attribute("companyos.equipment_tags", ",".join(equipment_tags))
        _start = time.perf_counter()
        response = chain.invoke({
            "query": query,
            "plant_context": plant_context,
            "conversation_history": json.dumps(conversation_history or []),
            "graph_context": graph_context,
            "equipment_context": equipment_context or "No specific equipment detected in query.",
            "oem_data": oem_data,
            "compliance_data": compliance_data,
            "sop_data": sop_data,
            "maintenance_data": maintenance_data,
            "incident_data": incident_data,
            "lessons_learned": lessons,
            "reflection_memory": reflection,
            "episodic_memory": json.dumps(episodic),
            "equipment_episodes": equipment_episodes or "No equipment-specific episodes.",
        })
        latency_ms = compute_latency_ms(_start, time.perf_counter())
        span.set_attribute("companyos.latency_ms", latency_ms)

    result = parse_llm_json(response.content)
    if result is None:
        # Fallback — return the raw text as the answer
        result = {
            "answer": response.content[:2000],
            "intent": "general_question",
            "citations": [],
            "sources_consulted": [],
            "follow_up_questions": [],
            "confidence_score": 25,
            "risk_level": "medium",
            "error": "Could not parse Search Agent JSON output",
        }

    cost = estimate_cost(settings.SEARCH_AGENT_MODEL, response)
    brain_output = parse_brain_output(result, "SEARCH_AGENT", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    # Save as episodic — optionally tagged to equipment
    primary_tag = equipment_tags[0] if equipment_tags else ""
    memory.save_episodic_industrial(
        "SEARCH_AGENT", query, flat,
        equipment_tag=primary_tag,
        context_type="copilot_query",
    )
    evaluator.evaluate(flat, "SEARCH_AGENT", settings.SEARCH_AGENT_MODEL, latency_ms, run_id=run_id)

    return flat
