"""
Temporal Activities — CompanyOS V3.1 Layer 0 Workflow Orchestration.

Activities are where non-deterministic work (wall-clock time, DB writes, LLM
calls) belongs — Temporal Workflow code itself must stay deterministic since
it gets replayed.
"""
from datetime import datetime
from temporalio import activity

from agents.graph import run_pipeline
from api.routes import persist_pipeline_results

# Moved from clawbot.py — simulates fetching an industry trend.
TRENDS = [
    "Review the latest Instagram algorithm trends for B2B SaaS and draft a lead gen campaign with a Reel.",
    "Analyze the impact of AI in fintech and create a LinkedIn sequence targeting CTOs.",
    "Research common drawbacks of SaaS pricing models and draft an email marketing campaign for enterprise clients.",
    "Analyze how mobile app startups are acquiring users in 2026 and draft social media posts to offer premium dev services.",
]


def _pick_trend() -> str:
    """Deterministic rotation based on the hour (moved from clawbot.py)."""
    return TRENDS[datetime.now().hour % len(TRENDS)]


@activity.defn
async def run_scheduled_pipeline_activity() -> dict:
    """
    Picks a goal and runs the full CompanyOS pipeline, persisting results as
    PipelineItems. Replaces clawbot.py's run_clawbot_cycle().
    """
    goal = _pick_trend()
    activity.logger.info(f"Selected goal: {goal}")

    final_state = await run_pipeline(goal)
    created_items = persist_pipeline_results(final_state, goal)

    return {
        "goal": goal,
        "items_created": created_items,
        "agents_run": final_state.get("completed_agents", []),
        "errors": final_state.get("errors", []),
    }
