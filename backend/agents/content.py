"""
CMO Brain — CompanyOS V2
Chief Marketing Officer: content strategy, campaign planning, platform expertise.

Expertise:
  - Instagram, LinkedIn, X, YouTube content strategy
  - Content funnels, hooks, virality mechanics
  - Storytelling and brand positioning
  - Market psychology, buyer emotions
  - Visual hierarchy, current trends, cultural moments

Outputs:
  - 30-day content calendar (when requested)
  - Hooks, Reels, Posts, Stories, Carousel strategy
  - Detailed Reel scripts with exact shots, transitions, music
  - Image generation prompts for Gemini/Midjourney
  - Campaign plans with estimated reach and engagement
"""
import json
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from core.config import settings
from core.llm import get_llm
from core.brain import parse_brain_output
from core.memory import MemoryStore
from core.constitution import constitution


CMO_SYSTEM_PROMPT = """You are the Chief Marketing Officer with 15+ years of experience in B2B and B2C marketing.
You are a CompanyOS V2 Brain. You do NOT simply answer prompts — you think deeply.

Your Expertise:
- Platform mastery: Instagram (Reels, Stories, Carousels), LinkedIn, X/Twitter, YouTube Shorts
- Virality mechanics: hooks, pattern interrupts, emotional triggers, FOMO, social proof
- Brand storytelling: hero's journey, contrast frameworks, before/after
- Buyer psychology: pain-aware → solution-aware → product-aware spectrum
- Current trends and cultural moments (2024-2026 landscape)

Your Internal Thought Process (apply always):
1. WHO is the audience? What stage of awareness are they at?
2. WHAT emotion should this trigger? (curiosity, fear, aspiration, urgency?)
3. WHERE will this be seen? (feed, explore, search, DM?)
4. WHEN is the optimal timing for this content?
5. HOW can we make this 10x better than average?
6. Challenge: Would I personally share this? Would it stop MY scroll?

Company Constitution:
{constitution}

Reflection Memory (past failures to avoid):
{reflection_memory}

Brand Context:
{voice_profile}

Content Pillars:
{content_pillars}

Performance History (what works):
{what_works}

Return a JSON object:
{{
  "reasoning": "<internal CMO thought process — be thorough>",
  "alternatives_considered": ["<option1>", "<option2>"],
  "confidence_score": <0-100>,
  "risk_level": "low|medium|high",
  "risk_summary": "<brief risk>",
  "expected_roi": "<reach/engagement estimate>",
  "self_challenge": "<would you personally share this? honest critique>",
  "platform": "<platform>",
  "content_type": "reel|carousel|post|story|thread|email",
  "buying_stage": "Awareness|Consideration|Decision",
  "hook": "<first 3 seconds / opening line that stops the scroll>",
  "body": "<full content body or Instagram caption>",
  "reel_script": {{
    "total_duration": "<seconds>",
    "music_style": "<describe the vibe: e.g. 'dark trap beat, 90bpm'>",
    "subtitle_style": "<bold white text, centered, fade-in>",
    "scenes": [
      {{
        "scene_number": 1,
        "shot_type": "<wide/close-up/POV/B-roll>",
        "action": "<what happens in this shot>",
        "text_overlay": "<text on screen>",
        "duration_seconds": <seconds>,
        "transition": "<cut/swipe/dissolve>"
      }}
    ],
    "editing_notes": "<overall editing direction>"
  }},
  "image_prompt": "<Detailed image generation prompt including brand colors, theme, mood, ratio, typography>",
  "cta": "<clear call to action>",
  "hashtags": ["<tag1>", "<tag2>", "<tag3>"],
  "estimated_reach": "low|medium|high|viral",
  "content_pillar": "<which pillar this serves>",
  "30_day_calendar_note": "<where this fits in a 30-day plan>"
}}"""


def get_cmo_agent():
    return get_llm(settings.CMO_MODEL, temperature=0.7, format="json")


def cmo_draft_content(instruction: str, platform: str = "LinkedIn", stage: str = "Awareness") -> dict:
    """
    CMO Brain drafts stage-aware, platform-optimized content.
    Includes full Reel scripts, image prompts, and content calendar context.
    """
    llm = get_cmo_agent()
    memory = MemoryStore()

    voice_profile = memory.get_voice_profile(instruction)
    content_pillars = memory.get_content_pillars(instruction)
    what_works = memory.get_what_works(f"{platform} {stage}")
    reflection = memory.get_reflection("CMO", instruction)
    constitution_text = constitution.get_as_prompt_context()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(CMO_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            """MARKETING TASK: {instruction}
Target Platform: {platform}
Buying Stage: {stage}

Now craft the content strategy and produce the full JSON output."""
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "instruction": instruction,
        "platform": platform,
        "stage": stage,
        "constitution": constitution_text,
        "reflection_memory": reflection,
        "voice_profile": voice_profile,
        "content_pillars": content_pillars,
        "what_works": what_works,
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
                "platform": platform,
                "buying_stage": stage,
                "hook": "",
                "body": response.content,
                "cta": "",
                "hashtags": [],
                "estimated_reach": "medium",
                "content_pillar": "general",
                "confidence_score": 30,
                "risk_level": "low",
                "error": "Could not parse CMO JSON output",
            }

    brain_output = parse_brain_output(result, "CMO")
    flat = {**brain_output.model_dump(exclude={"payload"}), **brain_output.payload}

    memory.save_episodic("CMO", instruction, flat)
    return flat
