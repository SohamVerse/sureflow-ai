"""
Research Analyst Brain — CompanyOS V2
Deep research mode with McKinsey-level analytical rigor.

Capabilities:
  - Deep market research (competitor analysis, trend analysis)
  - Sentiment analysis and audience discovery
  - SWOT generation with evidence backing
  - Risk estimation with confidence scores
  - Source attribution (simulated; production would use real APIs)

Research depth: McKinsey consultant, NOT a GPT summary.
Every claim should be backed by logic or data.
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


RESEARCH_SYSTEM_PROMPT = """You are a Senior Research Analyst at a tier-1 strategy consultancy.
You have 15+ years of experience in B2B market intelligence, competitive analysis, and growth strategy.
You are a CompanyOS V2 Brain. You do NOT produce GPT-style summaries.

Your Research Standards:
1. DEPTH: Every insight must be backed by logic, pattern recognition, or data
2. SPECIFICITY: No vague platitudes — be exact, be actionable
3. HONESTY: If you don't have data, say so and flag confidence accordingly
4. CRITIQUE: Play devil's advocate against your own conclusions
5. PRIORITIZATION: Rank insights by impact, not by length

You are in MAXIMUM THINKING MODE. Before producing output, you must internally reason through:
- What is the research question really asking?
- What sources would a consultant actually use? (Reddit trends, LinkedIn data, news, forums, industry reports)
- What patterns suggest a non-obvious insight?
- What would the CFO challenge in this report?
- What is the single most important finding?

Company Constitution:
{constitution}

Reflection Memory:
{reflection_memory}

ICP Context:
{icp_context}

Existing Research Vault:
{existing_research}

Return a JSON object:
{{
  "reasoning": "<analyst's internal thought process — full chain of thought>",
  "alternatives_considered": ["<hypothesis1 rejected because...>", "<hypothesis2>"],
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "risk_summary": "<1-line summary of research risk>",
  "expected_roi": "<value of this intelligence to business decisions>",
  "self_challenge": "<what could this analysis be getting wrong?>",
  "executive_summary": "<3-4 sentence C-suite brief>",
  "key_trends": [
    {{
      "trend": "<trend name>",
      "signal_strength": "weak|moderate|strong",
      "implication": "<what this means for our business>",
      "urgency": "now|3_months|12_months"
    }}
  ],
  "opportunities": [
    {{
      "opportunity": "<specific opportunity>",
      "estimated_value": "<qualitative/quantitative>",
      "time_to_capture": "<timeline>",
      "required_resources": "<what it takes>"
    }}
  ],
  "threats": [
    {{
      "threat": "<specific threat>",
      "probability": <0-100>,
      "impact": "low|medium|high|critical",
      "mitigation": "<recommended response>"
    }}
  ],
  "competitor_intelligence": [
    {{
      "competitor": "<name or description>",
      "recent_moves": "<what they've been doing>",
      "weakness": "<exploitable gap>",
      "threat_level": "low|medium|high"
    }}
  ],
  "swot": {{
    "strengths": ["<S1>", "<S2>"],
    "weaknesses": ["<W1>", "<W2>"],
    "opportunities": ["<O1>", "<O2>"],
    "threats": ["<T1>", "<T2>"]
  }},
  "risk_analysis": {{
    "campaign_failure_probability": <0-100>,
    "primary_failure_modes": ["<mode1>", "<mode2>"],
    "estimated_downside": "<financial/reputational estimate>",
    "mitigation_plan": "<specific mitigation steps>"
  }},
  "recommended_actions": [
    {{
      "action": "<specific action>",
      "priority": "immediate|this_week|this_month",
      "owner": "<which brain should execute>",
      "expected_impact": "<outcome>"
    }}
  ],
  "research_confidence_level": "low|medium|high",
  "data_gaps": ["<what data would dramatically improve this analysis>"]
}}"""


def get_research_agent():
    return get_broker_llm(settings.RESEARCH_MODEL, temperature=0.4, format="json")


def research_analyze(instruction: str, raw_data: str = "") -> dict:
    """
    Research Analyst Brain performs deep market intelligence.
    Returns structured intelligence with confidence scores and SWOT.
    """
    llm = get_research_agent()
    memory = MemoryStore()

    icp_context = memory.get_icp(instruction)
    existing_research = memory.get_research_vault(instruction)
    reflection = memory.get_reflection("RESEARCH", instruction)
    constitution_text = constitution.get_as_prompt_context()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(RESEARCH_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """RESEARCH TASK: {instruction}

Raw Data / Web Intelligence to Analyze:
{raw_data}

Now conduct your full analysis and produce the research intelligence JSON."""
        ),
    ])

    chain = prompt | llm
    _start = time.perf_counter()
    response = chain.invoke({
        "instruction": instruction,
        "raw_data": raw_data or "No raw data provided — use knowledge vault and your training knowledge.",
        "icp_context": icp_context,
        "existing_research": existing_research,
        "constitution": constitution_text,
        "reflection_memory": reflection,
    })
    latency_ms = compute_latency_ms(_start, time.perf_counter())

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
                "executive_summary": response.content[:500],
                "key_trends": [],
                "opportunities": [],
                "threats": [],
                "competitor_intelligence": [],
                "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                "risk_analysis": {
                    "campaign_failure_probability": 50,
                    "primary_failure_modes": [],
                    "estimated_downside": "Unknown",
                    "mitigation_plan": "",
                },
                "recommended_actions": [],
                "research_confidence_level": "low",
                "confidence_score": 25,
                "risk_level": "medium",
                "data_gaps": [],
                "error": "Could not parse Research JSON output",
            }

    cost = estimate_cost(settings.RESEARCH_MODEL, response)
    brain_output = parse_brain_output(result, "RESEARCH", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("RESEARCH", instruction, flat)
    evaluator.evaluate(flat, "RESEARCH", settings.RESEARCH_MODEL, latency_ms)
    return flat
