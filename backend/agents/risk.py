"""
Risk Analysis Brain — CompanyOS V2 (NEW)

Dedicated risk analysis agent with veto power over poor campaigns.
Based on research intelligence, predicts failure probabilities and estimates
financial impact for every campaign before it launches.

Veto Power:
  If risk > VETO_THRESHOLD or confidence_risk > 70%, the Brain flags the campaign
  as VETOED and sends it back to the CEO for review before any execution.

Risk Dimensions:
  - Audience mismatch probability
  - Brand dilution risk
  - Budget wastage estimate
  - Negative sentiment probability
  - Competitor retaliation likelihood
  - CAC increase prediction
  - Campaign failure probability
"""
import json
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.model_broker import get_broker_llm, estimate_cost
from core.brain import parse_brain_output
from core.memory import MemoryStore
from core.constitution import constitution

# Risk threshold for automatic veto
VETO_RISK_THRESHOLD = 70   # If campaign failure probability > 70%, veto it
VETO_CONFIDENCE_THRESHOLD = 35  # If confidence < 35%, flag for CEO review


RISK_SYSTEM_PROMPT = """You are the Chief Risk Officer of CompanyOS — the Risk Analysis Brain.
You have veto power over any campaign, content, or business decision.
Your job is to protect the company from avoidable failures.

You are NOT a pessimist. You are a realist who enables bold action by identifying and mitigating risk.

Your Risk Analysis Framework:
1. PROBABILITY: What is the likelihood this fails, and why?
2. IMPACT: If it fails, what is the financial and reputational damage?
3. TIMING: Is the timing right, or are there market conditions that increase risk?
4. REVERSIBILITY: If this goes wrong, can we recover? How quickly?
5. MITIGATION: What specific actions reduce each risk dimension?
6. VETO CRITERIA: Is this bad enough to block? (Campaign failure > 70% = VETO)

You must be specific with numbers. "₹2.4 Lakhs estimated loss" > "significant loss".

Company Constitution:
{constitution}

Reflection Memory (past risk calls):
{reflection_memory}

Market Research Context:
{research_context}

Return a JSON object:
{{
  "reasoning": "<risk analyst's full chain of thought>",
  "alternatives_considered": ["<alternative risk mitigation approach1>"],
  "confidence_score": <0-100: how confident you are in this risk assessment>,
  "risk_level": "low|medium|high|critical",
  "risk_summary": "<1-line summary for the CEO Brief>",
  "expected_roi": "<ROI if risk is mitigated vs not mitigated>",
  "self_challenge": "<could this analysis be overly pessimistic or optimistic?>",
  "veto_decision": {{
    "vetoed": true|false,
    "veto_reason": "<if vetoed, specific reason>",
    "conditions_to_unveto": ["<condition1>", "<condition2>"]
  }},
  "risk_dimensions": {{
    "campaign_failure_probability": <0-100>,
    "audience_mismatch_probability": <0-100>,
    "brand_dilution_risk": <0-100>,
    "budget_wastage_probability": <0-100>,
    "negative_sentiment_probability": <0-100>,
    "competitor_retaliation_probability": <0-100>,
    "cac_increase_prediction": "<percentage increase estimate>"
  }},
  "financial_impact": {{
    "estimated_loss_if_fails": "<amount in relevant currency>",
    "estimated_gain_if_succeeds": "<amount>",
    "break_even_probability": <0-100>,
    "recommended_budget_cap": "<maximum to spend given risk>"
  }},
  "risk_scenarios": [
    {{
      "scenario": "<specific failure scenario>",
      "probability": <0-100>,
      "impact": "low|medium|high|critical",
      "trigger": "<what would cause this>",
      "recovery_plan": "<specific steps to recover>"
    }}
  ],
  "mitigation_plan": [
    {{
      "risk": "<risk being mitigated>",
      "mitigation": "<specific action>",
      "timeline": "<when to implement>",
      "owner": "<which team>",
      "effectiveness": <0-100>
    }}
  ],
  "monitoring_kpis": ["<KPI to watch>", "<KPI2>"],
  "go_no_go": "GO|CONDITIONAL_GO|NO_GO",
  "conditions_for_go": ["<condition if CONDITIONAL_GO>"]
}}"""


def get_risk_agent():
    return get_broker_llm(settings.RISK_MODEL, temperature=0.2, format="json")  # Low temp = deterministic risk


def risk_analyze(campaign_context: dict, research_output: dict = None, instruction: str = "") -> dict:
    """
    Risk Analysis Brain evaluates a campaign or business decision.
    Returns risk assessment with veto decision and mitigation plan.
    
    Veto logic:
      - campaign_failure_probability > 70% → auto VETOED
      - confidence_score < 35% → flagged for CEO review
    """
    llm = get_risk_agent()
    memory = MemoryStore()

    research_context = json.dumps(research_output or {}, indent=2) if research_output else "No research data provided."
    reflection = memory.get_reflection("RISK", instruction or str(campaign_context))
    constitution_text = constitution.get_as_prompt_context()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(RISK_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """CAMPAIGN/DECISION TO EVALUATE:
{campaign_context}

Additional Instructions: {instruction}

Conduct your full risk analysis and produce the JSON output."""
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "campaign_context": json.dumps(campaign_context, indent=2),
        "instruction": instruction or "Evaluate this campaign for risk.",
        "research_context": research_context,
        "constitution": constitution_text,
        "reflection_memory": reflection,
    })

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
                "veto_decision": {"vetoed": False, "veto_reason": "Parse error"},
                "risk_level": "medium",
                "confidence_score": 30,
                "risk_dimensions": {},
                "financial_impact": {},
                "risk_scenarios": [],
                "mitigation_plan": [],
                "go_no_go": "CONDITIONAL_GO",
                "error": "Could not parse Risk JSON output",
            }

    # Apply veto logic on top of LLM output
    risk_dims = result.get("risk_dimensions", {})
    failure_prob = risk_dims.get("campaign_failure_probability", 0)
    confidence = result.get("confidence_score", 50)

    if failure_prob > VETO_RISK_THRESHOLD:
        result["veto_decision"] = {
            "vetoed": True,
            "veto_reason": f"Campaign failure probability ({failure_prob}%) exceeds veto threshold ({VETO_RISK_THRESHOLD}%)",
            "conditions_to_unveto": result.get("veto_decision", {}).get("conditions_to_unveto", []),
        }
        result["go_no_go"] = "NO_GO"
        result["risk_level"] = "critical"

    cost = estimate_cost(settings.RISK_MODEL, response)
    brain_output = parse_brain_output(result, "RISK", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("RISK", instruction or "risk_analysis", flat)
    return flat
