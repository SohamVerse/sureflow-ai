"""
Temporal Worker — CompanyOS V3.1 Layer 0 Workflow Orchestration.

Run this instead of `python clawbot.py`. Connects to the dockerized Temporal
server, ensures the hourly schedule exists (idempotent — safe to restart),
and polls the task queue for workflow/activity work.
"""
import asyncio
import logging
from datetime import timedelta

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleAlreadyRunningError,
    ScheduleIntervalSpec,
    ScheduleSpec,
)
from temporalio.worker import Worker

from workflows.activities import run_scheduled_pipeline_activity, generate_benchmarks_activity
from workflows.cron_workflow import ScheduledPipelineWorkflow, BenchmarkGenerationWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("companyos.worker")

TEMPORAL_ADDRESS = "localhost:7233"
TASK_QUEUE = "companyos-pipeline"


async def ensure_schedule(
    client: Client,
    schedule_id: str,
    workflow_run_fn,
    workflow_id: str,
    interval: timedelta,
    trigger_immediately: bool = False,
) -> None:
    """Idempotently create a Schedule for a workflow — safe to call on every worker restart."""
    try:
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    workflow_run_fn,
                    id=workflow_id,
                    task_queue=TASK_QUEUE,
                ),
                spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=interval)]),
            ),
            trigger_immediately=trigger_immediately,
        )
        logger.info(f"Created schedule '{schedule_id}' (every {interval}).")
    except ScheduleAlreadyRunningError:
        logger.info(f"Schedule '{schedule_id}' already exists — skipping creation.")


async def main():
    client = await Client.connect(TEMPORAL_ADDRESS)

    # Hourly pipeline run — replaces clawbot.py, preserves its "run once on start".
    await ensure_schedule(
        client,
        schedule_id="companyos-hourly-pipeline",
        workflow_run_fn=ScheduledPipelineWorkflow.run,
        workflow_id="companyos-scheduled-pipeline",
        interval=timedelta(hours=1),
        trigger_immediately=True,
    )
    # Daily benchmark rollup — see evaluation/evaluator.py.
    await ensure_schedule(
        client,
        schedule_id="companyos-daily-benchmarks",
        workflow_run_fn=BenchmarkGenerationWorkflow.run,
        workflow_id="companyos-benchmark-generation",
        interval=timedelta(days=1),
    )

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ScheduledPipelineWorkflow, BenchmarkGenerationWorkflow],
        activities=[run_scheduled_pipeline_activity, generate_benchmarks_activity],
    )
    logger.info(f"🚀 CompanyOS Temporal Worker started on task queue '{TASK_QUEUE}'.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
