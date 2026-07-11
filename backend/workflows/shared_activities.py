"""
Shared Temporal Activities — cross-cutting work not specific to any one
agent family (currently just the daily benchmark rollup, which iterates
every live agent/model pair regardless of which product area it belongs to).
"""
from datetime import timedelta
from temporalio import activity

from evaluation.evaluator import evaluator, AGENT_MODELS


@activity.defn
async def generate_benchmarks_activity() -> dict:
    """
    Generates a daily Benchmark snapshot for every live agent/model pair (see
    evaluation/evaluator.py::EvaluatorBrain.generate_benchmark). Agent/model
    pairs with no Evaluation rows in the window are skipped, not fabricated.
    """
    generated = []
    skipped = []
    for agent_id, model_name in AGENT_MODELS.items():
        benchmark = evaluator.generate_benchmark(agent_id, model_name, timedelta(days=1))
        if benchmark:
            generated.append(f"{agent_id}/{model_name}")
        else:
            skipped.append(f"{agent_id}/{model_name}")

    activity.logger.info(f"Benchmarks generated: {generated}, skipped (no data): {skipped}")
    return {"generated": generated, "skipped": skipped}
