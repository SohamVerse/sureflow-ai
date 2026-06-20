"""
CEO Brain — CompanyOS V2
Executive reasoning, department orchestration, conflict resolution.

Inspired by the combined reasoning style of:
  Satya Nadella (empathy + cloud-scale thinking)
  Jensen Huang (relentless execution + hardware-software co-design mindset)
  Elon Musk (first-principles + extreme ownership)
  Naval Ravikant (leverage + wealth creation clarity)

Capabilities:
  - Strategic goal decomposition
  - KPI-aware routing decisions  
  - Conflict resolution between departments
  - Budget and priority allocation
  - Fundraising & revenue planning awareness
  - Weekly CEO Brief generation
  - Growth opportunity identification
"""
import json
import time
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.model_broker import get_broker_llm, estimate_cost
from core.brain import parse_brain_output
from core.memory import MemoryStore
from core.constitution import constitution
from evaluation.evaluator import evaluator
from evaluation.metrics import compute_latency_ms


CEO_SYSTEM_PROMPT = """You are the CEO of a high-growth company operating through CompanyOS V2.
You think like a synthesis of Satya Nadella, Jensen Huang, Elon Musk, and Naval Ravikant.

Your Decision Framework (mandatory — apply before every output):
1. UNDERSTAND: What is the REAL goal beneath the stated goal?
2. DECOMPOSE: Break it into specialist tasks (CMO, RESEARCH, SDR, AE, RISK, EMAIL).
3. CHALLENGE: What am I missing? What assumptions am I making? What could destroy this plan?
4. PRIORITIZE: Allocate by impact-to-effort ratio.
5. SYNTHESIZE: Produce a routing plan with explicit reasoning.

You have access to:
- Company Knowledge Vault (ICP, Voice Profile, Content Pillars, Research, What Works)
- Reflection Memory (past failures and lessons)
- Episodic Memory (what was run before)
- Company Constitution

{constitution}

REFLECTION MEMORY:
{reflection_memory}

RECENT EPISODES:
{episodic_memory}

Always think: "Would I make this decision if this was my own company and my own money?"

Return a JSON object with this EXACT schema:
{{
  "objective": "<clear, refined goal statement>",
  "reasoning": "<CEO's internal thought process — be honest about uncertainties>",
  "alternatives_considered": ["<option1>", "<option2>"],
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high|critical",
  "risk_summary": "<1 sentence risk description>",
  "expected_roi": "<qualitative or quantitative ROI estimate>",
  "priority": "high|medium|low",
  "tasks": [
    {{"agent": "CMO", "instruction": "<specific task>", "priority": "high|medium|low"}},
    {{"agent": "RESEARCH", "instruction": "<specific task>", "priority": "high|medium|low"}},
    {{"agent": "SDR", "instruction": "<specific task>", "priority": "high|medium|low"}},
    {{"agent": "AE", "instruction": "<specific task>", "priority": "high|medium|low"}},
    {{"agent": "RISK", "instruction": "<what to analyze>", "priority": "high|medium|low"}},
    {{"agent": "EMAIL", "instruction": "<outreach task>", "priority": "high|medium|low"}}
  ],
  "resource_allocation": {{
    "estimated_budget": "<budget estimate>",
    "timeline": "<execution timeline>",
    "team_focus": "<which departments should lead>"
  }},
  "growth_opportunity": "<specific growth opportunity identified>",
  "ceo_brief_summary": "<3-4 sentence executive summary for the weekly brief>",
  "self_challenge": "<honest critique: what could go wrong? what am I not seeing?>"
}}

Only include agents that are genuinely needed. Omit irrelevant ones.
Never include an agent just to look thorough — that wastes resources."""


def get_ceo_agent():
    return get_broker_llm(settings.CEO_MODEL, temperature=0.3, format="json")


def ceo_analyze(goal: str, context: dict = None) -> dict:
    """
    CEO analyzes a high-level goal and produces a routing plan.
    Queries ICP, Voice, and Research collections from Knowledge Vault.
    Incorporates Reflection Memory to avoid past mistakes.
    """
    llm = get_ceo_agent()
    memory = MemoryStore()

    # Retrieve multi-source RAG context
    icp_context = memory.get_icp(goal)
    voice_context = memory.get_voice_profile(goal)
    research_context = memory.get_research_vault(goal)
    reflection = memory.get_reflection("CEO", goal)
    episodes = memory.get_episodic("CEO", limit=3)
    constitution_text = constitution.get_as_prompt_context()

    episodic_text = "\n".join([
        f"• [{e['timestamp'][:10]}] {e['output_summary']}"
        for e in episodes
    ]) or "No recent CEO episodes."

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(CEO_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """GOAL: {goal}

ICP Context from Knowledge Vault:
{icp_context}

Voice Profile:
{voice_context}

Research Intelligence:
{research_context}

Additional Context: {extra_context}

Now perform your CEO analysis and produce the routing plan JSON."""
        ),
    ])

    chain = prompt | llm
    _start = time.perf_counter()
    response = chain.invoke({
        "goal": goal,
        "icp_context": icp_context,
        "voice_context": voice_context,
        "research_context": research_context,
        "extra_context": str(context) if context else "None provided.",
        "constitution": constitution_text,
        "reflection_memory": reflection,
        "episodic_memory": episodic_text,
    })
    latency_ms = compute_latency_ms(_start, time.perf_counter())

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # Strip markdown fences if Gemini wraps with ```json
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        try:
            result = json.loads(content)
        except Exception:
            result = {
                "objective": goal,
                "tasks": [],
                "priority": "medium",
                "reasoning": response.content,
                "confidence_score": 30,
                "risk_level": "medium",
                "risk_summary": "Could not parse CEO output",
                "expected_roi": "Unknown",
                "alternatives_considered": [],
                "self_challenge": "Parsing failed",
                "ceo_brief_summary": goal,
                "growth_opportunity": "",
                "resource_allocation": {},
                "error": "Could not parse CEO JSON output",
            }

    # Normalize to the canonical BrainOutput contract
    cost = estimate_cost(settings.CEO_MODEL, response)
    brain_output = parse_brain_output(result, "CEO", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    # Persist to memory
    memory.save_episodic("CEO", goal, flat)
    evaluator.evaluate(flat, "CEO", settings.CEO_MODEL, latency_ms)
    return flat
