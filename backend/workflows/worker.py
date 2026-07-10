"""
Temporal Worker — CompanyOS V3.1 Layer 0 Workflow Orchestration.

Run this instead of `python clawbot.py`. Connects to the dockerized Temporal
server, ensures the hourly schedule exists (idempotent — safe to restart),
and polls the task queue for workflow/activity work.
"""
import asyncio
import logging
import sys
from datetime import timedelta

# Agent node functions (agents/graph.py) print emoji status lines. On Windows,
# this worker's stdout defaults to the system codepage (e.g. cp1252) rather
# than UTF-8, which raises UnicodeEncodeError on the first emoji print and
# fails the activity (this crashed the very first scheduled pipeline run).
# Reconfiguring here makes stdout/stderr tolerant of any Unicode regardless
# of how this process is launched or its output redirected.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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

# Industrial workflows and activities (Phase 3)
from workflows.industrial_activities import (
    ocr_extract_activity,
    doc_intelligence_activity,
    embed_and_store_activity,
    update_industrial_graph_activity,
    maintenance_analysis_activity,
    record_work_order_activity,
    lessons_learned_activity,
    compliance_audit_activity,
    copilot_query_activity,
)
from workflows.industrial_workflows import (
    DocumentIngestionWorkflow,
    MaintenanceLifecycleWorkflow,
    LessonsLearnedWorkflow,
)

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
        workflows=[
            ScheduledPipelineWorkflow,
            BenchmarkGenerationWorkflow,
            # Industrial workflows (Phase 3)
            DocumentIngestionWorkflow,
            MaintenanceLifecycleWorkflow,
            LessonsLearnedWorkflow,
        ],
        activities=[
            run_scheduled_pipeline_activity,
            generate_benchmarks_activity,
            # Industrial activities (Phase 3)
            ocr_extract_activity,
            doc_intelligence_activity,
            embed_and_store_activity,
            update_industrial_graph_activity,
            maintenance_analysis_activity,
            record_work_order_activity,
            lessons_learned_activity,
            compliance_audit_activity,
            copilot_query_activity,
        ],
    )
    logger.info(f"🚀 CompanyOS Temporal Worker started on task queue '{TASK_QUEUE}'.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

