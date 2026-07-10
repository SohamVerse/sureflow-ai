"""
Temporal Workflow — CompanyOS V3.1 Layer 0 Workflow Orchestration.

Runs on a Temporal Schedule (see workflows/worker.py) and gets automatic
retries on the underlying activity — a transient failure no longer just
silently drops the cycle.
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.shared_activities import generate_benchmarks_activity


@workflow.defn
class BenchmarkGenerationWorkflow:
    """Daily benchmark rollup — see evaluation/evaluator.py."""

    @workflow.run
    async def run(self) -> dict:
        return await workflow.execute_activity(
            generate_benchmarks_activity,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
