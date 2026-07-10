"""
Temporal Worker — SureFlow OS Industrial Intelligence Workflow Orchestration.

Connects to the dockerized Temporal server, ensures the daily benchmark
schedule exists (idempotent — safe to restart), and polls the task queue
for workflow/activity work.
"""
import asyncio
import logging
import sys
from datetime import timedelta

# Log lines below use emoji. On Windows, this worker's stdout defaults to the
# system codepage (e.g. cp1252) rather than UTF-8, which raises
# UnicodeEncodeError on the first emoji print and crashes the process.
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

from workflows.shared_activities import generate_benchmarks_activity
from workflows.cron_workflow import BenchmarkGenerationWorkflow

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
            BenchmarkGenerationWorkflow,
            # Industrial workflows (Phase 3)
            DocumentIngestionWorkflow,
            MaintenanceLifecycleWorkflow,
            LessonsLearnedWorkflow,
        ],
        activities=[
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
    logger.info(f"🚀 SureFlow Temporal Worker started on task queue '{TASK_QUEUE}'.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
