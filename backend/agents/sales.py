"""
SDR & Account Executive Brains — CompanyOS V2

SDR Brain:
  - Lead qualification and ICP scoring
  - Lead rejection (can say NO to poor leads)
  - Objection handling anticipation
  - Meeting booking recommendations

AE Brain:
  - Proposal creation and negotiation strategy
  - Pricing recommendations
  - Revenue forecasting
  - Deal risk estimation
  - Upselling identification
"""
import json
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.model_broker import get_broker_llm, estimate_cost
from core.brain import parse_brain_output
from core.memory import MemoryStore
from core.constitution import constitution


SDR_SYSTEM_PROMPT = """You are a Senior SDR (Sales Development Representative) with 15+ years of B2B sales experience.
You are a CompanyOS V2 Brain. You think like a top-performing SDR who has closed 100+ enterprise deals.

Your Philosophy:
  - You REJECT poor leads. A wasted outreach burns credibility and CAC.
  - You qualify relentlessly. One great lead > ten mediocre ones.
  - You read between the lines. Company size, tech stack, growth signals all matter.
  - You personalize everything. Generic outreach is spam.

Decision Framework:
1. Does this lead match our ICP? Score them honestly.
2. What is their buying stage? What pains are they feeling right now?
3. Would outreach to them be welcome or intrusive?
4. What is the highest-leverage opening message?
5. Challenge: Would I genuinely want this company as a client?

Company Constitution:
{constitution}

ICP Definition:
{icp_context}

Reflection Memory:
{reflection_memory}

Return a JSON object:
{{
  "reasoning": "<SDR's internal analysis — think out loud about this lead>",
  "alternatives_considered": ["<approach 1 considered>", "<approach 2>"],
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "risk_summary": "<risk of outreach backfiring>",
  "expected_roi": "<expected revenue opportunity if closed>",
  "self_challenge": "<would you genuinely chase this lead? be honest>",
  "lead_verdict": "REJECT|NURTURE|OUTREACH|ESCALATE_TO_AE",
  "rejection_reason": "<if REJECT: specific reason>",
  "icp_score": <0.0-10.0>,
  "icp_fit": "poor|fair|good|excellent",
  "icp_score_breakdown": {{
    "company_size": <0-10>,
    "industry_match": <0-10>,
    "title_authority": <0-10>,
    "pain_alignment": <0-10>,
    "budget_signal": <0-10>
  }},
  "buying_stage": "Unaware|Problem-Aware|Solution-Aware|Product-Aware|Decision",
  "pain_points_identified": ["<pain1>", "<pain2>"],
  "outreach_strategy": {{
    "channel": "email|linkedin|cold_call|warm_intro",
    "timing": "<best day/time to reach>",
    "tone": "formal|conversational|direct|empathetic"
  }},
  "outreach_message": "<personalized outreach under 120 words>",
  "subject_line": "<email/linkedin subject line>",
  "objection_anticipation": [
    {{
      "objection": "<anticipated objection>",
      "rebuttal": "<how to handle it>"
    }}
  ],
  "next_action": "<specific next step>",
  "follow_up_sequence": ["<Day 1: ...>", "<Day 3: ...>", "<Day 7: ...>"]
}}"""


AE_SYSTEM_PROMPT = """You are a Senior Account Executive (AE) with 15+ years closing complex B2B deals.
You are a CompanyOS V2 Brain. You think like a top-performing AE who understands buying committees, 
procurement processes, and executive psychology.

Your Expertise:
  - Proposal structuring and value quantification
  - Multi-stakeholder navigation (Champion, Economic Buyer, Blocker)
  - Pricing strategy and negotiation tactics
  - Revenue forecasting with probability weighting
  - Upselling and expansion revenue identification

Company Constitution:
{constitution}

ICP Context:
{icp_context}

Reflection Memory:
{reflection_memory}

Return a JSON object:
{{
  "reasoning": "<AE's internal deal analysis>",
  "alternatives_considered": ["<deal strategy 1>", "<strategy 2>"],
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "risk_summary": "<primary deal risk>",
  "expected_roi": "<expected ACV and total contract value>",
  "self_challenge": "<what could kill this deal? be honest>",
  "qualification_status": "QUALIFIED|UNQUALIFIED|NEEDS_MORE_INFO",
  "close_probability": <0-100>,
  "deal_stage": "Discovery|Evaluation|Proposal|Negotiation|Closing",
  "stakeholder_map": {{
    "champion": "<who is rooting for us internally>",
    "economic_buyer": "<who controls the budget>",
    "potential_blocker": "<who might kill the deal>"
  }},
  "proposed_solution": "<specific solution recommendation>",
  "pricing_recommendation": {{
    "tier": "<recommended pricing tier>",
    "rationale": "<why this tier fits>",
    "discount_ceiling": "<maximum discount to offer>",
    "upsell_opportunity": "<potential upsell>"
  }},
  "proposal_outline": ["<section1>", "<section2>", "<section3>"],
  "next_steps": ["<step1>", "<step2>"],
  "follow_up_message": "<professional follow-up under 200 words>",
  "objection_handling": [
    {{
      "objection": "<anticipated objection>",
      "response": "<AE response strategy>"
    }}
  ],
  "revenue_forecast": {{
    "expected_acv": "<annual contract value>",
    "close_date": "<expected close timeline>",
    "risk_adjusted_value": "<probability-weighted value>"
  }},
  "deal_notes": "<critical intelligence for CRM>"
}}"""


def get_sdr_agent():
    return get_broker_llm(settings.SDR_MODEL, temperature=0.3, format="json")


def get_ae_agent():
    return get_broker_llm(settings.AE_MODEL, temperature=0.4, format="json")


def sdr_score_lead(lead_data: dict, instruction: str = "") -> dict:
    """
    SDR Brain scores a lead against ICP, determines verdict (REJECT/NURTURE/OUTREACH/ESCALATE),
    and drafts personalized outreach with objection anticipation.
    """
    llm = get_sdr_agent()
    memory = MemoryStore()

    icp_context = memory.get_icp(f"{lead_data.get('company', '')} {lead_data.get('title', '')}")
    reflection = memory.get_reflection("SDR", str(lead_data))
    constitution_text = constitution.get_as_prompt_context()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SDR_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """LEAD DATA:
{lead_data}

Additional Instructions: {instruction}

Score and qualify this lead now."""
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "lead_data": json.dumps(lead_data, indent=2),
        "instruction": instruction or "Score this lead against our ICP and determine the best outreach strategy.",
        "icp_context": icp_context,
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
                "icp_score": 5.0,
                "icp_fit": "fair",
                "lead_verdict": "NURTURE",
                "buying_stage": "Unaware",
                "outreach_message": "",
                "subject_line": "",
                "confidence_score": 30,
                "risk_level": "medium",
                "error": "Could not parse SDR JSON output",
            }

    cost = estimate_cost(settings.SDR_MODEL, response)
    brain_output = parse_brain_output(result, "SDR", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("SDR", str(lead_data), flat)
    return flat


def ae_qualify_lead(lead_data: dict, conversation_history: str = "") -> dict:
    """
    AE Brain deeply qualifies a lead, maps stakeholders, recommends pricing,
    and produces a revenue forecast with probability-weighted deal value.
    """
    llm = get_ae_agent()
    memory = MemoryStore()

    icp_context = memory.get_icp(lead_data.get("company", ""))
    what_works = memory.get_what_works("closing deals B2B enterprise")
    reflection = memory.get_reflection("AE", str(lead_data))
    constitution_text = constitution.get_as_prompt_context()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(AE_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """LEAD DATA:
{lead_data}

Conversation History: {history}

What Closes Deals:
{what_works}

Qualify this lead and produce your full deal analysis."""
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "lead_data": json.dumps(lead_data, indent=2),
        "history": conversation_history or "No prior conversation on record.",
        "icp_context": icp_context,
        "what_works": what_works,
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
                "qualification_status": "NEEDS_MORE_INFO",
                "close_probability": 50,
                "deal_stage": "Discovery",
                "next_steps": [],
                "follow_up_message": response.content,
                "confidence_score": 30,
                "risk_level": "medium",
                "error": "Could not parse AE JSON output",
            }

    cost = estimate_cost(settings.AE_MODEL, response)
    brain_output = parse_brain_output(result, "AE", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("AE", str(lead_data), flat)
    return flat
