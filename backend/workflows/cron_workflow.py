"""
Temporal Workflow — CompanyOS V3.1 Layer 0 Workflow Orchestration.

Replaces clawbot.py's `schedule`-library polling loop. Runs on a Temporal
Schedule (see workflows/worker.py) and gets automatic retries on the
underlying activity — a transient Ollama/Gemini failure no longer just
silently drops the cycle, unlike clawbot.py.
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.activities import run_scheduled_pipeline_activity


@workflow.defn
class ScheduledPipelineWorkflow:
    @workflow.run
    async def run(self) -> dict:
        return await workflow.execute_activity(
            run_scheduled_pipeline_activity,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
