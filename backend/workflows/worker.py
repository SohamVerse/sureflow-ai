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

from workflows.activities import run_scheduled_pipeline_activity
from workflows.cron_workflow import ScheduledPipelineWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("companyos.worker")

TEMPORAL_ADDRESS = "localhost:7233"
TASK_QUEUE = "companyos-pipeline"
SCHEDULE_ID = "companyos-hourly-pipeline"


async def ensure_schedule(client: Client) -> None:
    """Idempotently create the hourly schedule (preserves clawbot's 'run once on start')."""
    try:
        await client.create_schedule(
            SCHEDULE_ID,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    ScheduledPipelineWorkflow.run,
                    id="companyos-scheduled-pipeline",
                    task_queue=TASK_QUEUE,
                ),
                spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=timedelta(hours=1))]),
            ),
            trigger_immediately=True,
        )
        logger.info(f"Created schedule '{SCHEDULE_ID}' (hourly, triggered immediately).")
    except ScheduleAlreadyRunningError:
        logger.info(f"Schedule '{SCHEDULE_ID}' already exists — skipping creation.")


async def main():
    client = await Client.connect(TEMPORAL_ADDRESS)
    await ensure_schedule(client)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ScheduledPipelineWorkflow],
        activities=[run_scheduled_pipeline_activity],
    )
    logger.info(f"🚀 CompanyOS Temporal Worker started on task queue '{TASK_QUEUE}'.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
