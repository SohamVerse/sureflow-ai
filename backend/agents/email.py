"""
Email Marketing Brain — CompanyOS V2

Capabilities:
  - Cold outreach, warm outreach, lead nurturing, proposal follow-up
  - Tone adaptation (formal/startup/enterprise/founder)
  - A/B testing variant generation
  - Open rate prediction
  - Reply probability estimation
  - Spam score awareness
"""
import json
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.model_broker import get_broker_llm, estimate_cost
from core.brain import parse_brain_output
from core.memory import MemoryStore
from core.constitution import constitution


EMAIL_SYSTEM_PROMPT = """You are a Senior Email Marketing Specialist and copywriter with 15+ years experience.
You are a CompanyOS V2 Brain. You write emails that get replied to.

Your Email Philosophy:
  - Every word must earn its place. Cut ruthlessly.
  - The subject line is the most important line. It determines if the email is read.
  - Personalization must feel genuine, not templated.
  - The opening hook is about THEM, not about you.
  - One CTA. Always one. Never two.

Tone Adaptation Matrix:
  - Enterprise executives: formal, data-driven, peer-to-peer, ROI-focused
  - Startup founders: conversational, direct, vision-aligned, time-aware
  - Mid-market managers: solution-focused, pain-aware, proof-heavy
  - SMB owners: relatable, specific to their industry, practical

Decision Framework:
1. WHO is this person and what do they care about most?
2. WHAT single pain point will my email address?
3. HOW do I open without talking about myself?
4. WHAT is the one ask — and is it low-enough friction?
5. WILL this pass a spam filter and a busy executive's 3-second scan?

Company Constitution:
{constitution}

Reflection Memory:
{reflection_memory}

Return a JSON object:
{{
  "reasoning": "<email strategist's thought process>",
  "alternatives_considered": ["<subject line variant A>", "<subject line variant B>"],
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "risk_summary": "<risk this email gets marked as spam or damages brand>",
  "expected_roi": "<expected reply rate and pipeline value>",
  "self_challenge": "<would a busy exec actually reply to this? be honest>",
  "email_type": "cold|warm|nurture|follow_up|re-engagement|event_invite",
  "tone": "formal|conversational|direct|empathetic",
  "primary_email": {{
    "subject_line": "<compelling subject, under 50 chars>",
    "preview_text": "<preview text shown in inbox, under 100 chars>",
    "opening_hook": "<first sentence — about THEM, not you>",
    "body": "<full email body>",
    "call_to_action": "<specific single CTA>",
    "signature_recommendation": "<how to sign off>"
  }},
  "ab_variants": [
    {{
      "variant": "A",
      "subject_line": "<variant A subject>",
      "opening_hook": "<variant A hook>",
      "rationale": "<why this variant might outperform>"
    }},
    {{
      "variant": "B",
      "subject_line": "<variant B subject>",
      "opening_hook": "<variant B hook>",
      "rationale": "<different emotional trigger tested>"
    }}
  ],
  "performance_predictions": {{
    "estimated_open_rate": "<percentage range>",
    "estimated_reply_rate": "<percentage range>",
    "spam_risk": "low|medium|high",
    "confidence": "<prediction confidence>"
  }},
  "personalization_tokens": ["<[FIRST_NAME]>", "<[COMPANY]>", "<[PAIN_POINT]>"],
  "follow_up_sequence": [
    {{"day": 3, "subject": "<follow-up subject>", "message": "<brief follow-up>"}},
    {{"day": 7, "subject": "<second follow-up>", "message": "<brief>"}},
    {{"day": 14, "subject": "<breakup email subject>", "message": "<breakup email>"}}
  ],
  "send_time_recommendation": "<best day and time to send>"
}}"""


def get_email_agent():
    return get_broker_llm(settings.EMAIL_MODEL, temperature=0.6, format="json")


def email_agent_draft(lead_data: dict, additional_context: str = "") -> dict:
    """
    Email Marketing Brain drafts high-converting outreach with A/B variants,
    performance predictions, and a full follow-up sequence.
    """
    llm = get_email_agent()
    memory = MemoryStore()

    voice = memory.get_voice_profile(f"email outreach {lead_data.get('title', '')}")
    reflection = memory.get_reflection("EMAIL", str(lead_data))
    constitution_text = constitution.get_as_prompt_context()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(EMAIL_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """LEAD PROFILE:
{lead_data}

Brand Voice:
{voice}

Additional Context / Campaign Instructions:
{context}

Draft the full email strategy and produce the JSON output."""
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "lead_data": json.dumps(lead_data, indent=2),
        "voice": voice,
        "context": additional_context or "Standard outreach.",
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
                "primary_email": {
                    "subject_line": "Following up",
                    "body": response.content,
                    "call_to_action": "Let's connect",
                },
                "performance_predictions": {
                    "estimated_open_rate": "Unknown",
                    "spam_risk": "medium",
                },
                "confidence_score": 25,
                "risk_level": "medium",
                "error": "Could not parse Email JSON output",
            }

    cost = estimate_cost(settings.EMAIL_MODEL, response)
    brain_output = parse_brain_output(result, "EMAIL", cost=cost)
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("EMAIL", str(lead_data), flat)
    return flat
