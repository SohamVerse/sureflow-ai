"""
EvaluatorBrain — CompanyOS V3.1 Layer 2.

Measures cognitive quality and benchmarks brains, feeding empirical data into
the MetaLearning layer (Phase 5). See evaluation/models.py for the schema and
the module docstring there for which metrics are honestly computable today
versus pending real ground-truth outcome data.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone

from core.config import settings
from core.database import SessionLocal
from evaluation.models import Evaluation, Benchmark
from evaluation.metrics import (
    is_schema_valid,
    is_vetoed,
    requires_approval,
    compute_benchmark_aggregates,
)

logger = logging.getLogger("companyos.evaluator")

# The 7 live pipeline agents and the model setting each one is currently
# configured to use (see core/config.py). Shared by workflows/activities.py
# (benchmark scheduling) and api/routes.py (the benchmark API) — kept here
# rather than in workflows/activities.py to avoid a circular import, since
# that module imports api.routes.persist_pipeline_results.
AGENT_MODELS = {
    "CEO": settings.CEO_MODEL,
    "CMO": settings.CMO_MODEL,
    "RESEARCH": settings.RESEARCH_MODEL,
    "SDR": settings.SDR_MODEL,
    "AE": settings.AE_MODEL,
    "RISK": settings.RISK_MODEL,
    "EMAIL": settings.EMAIL_MODEL,
    # Industrial Intelligence Agents (Phase 2)
    "DOC_INTELLIGENCE": settings.DOC_INTELLIGENCE_MODEL,
    "KG_AGENT": settings.KG_AGENT_MODEL,
    "SEARCH_AGENT": settings.SEARCH_AGENT_MODEL,
    "MAINTENANCE": settings.MAINTENANCE_MODEL,
    "LESSONS_LEARNED": settings.LESSONS_LEARNED_MODEL,
    "COMPLIANCE": settings.COMPLIANCE_MODEL,
}


class EvaluatorBrain:
    """Evaluates BrainOutputs and generates aggregated benchmarks."""

    def evaluate(
        self,
        output: dict,
        agent_id: str,
        model_name: str,
        latency_ms: int,
        constitution_violation_count: int = 0,
        run_id: str | None = None,
    ) -> Evaluation:
        """
        Persist one Evaluation row for a completed agent call.

        `constitution_violation_count` defaults to 0: today only
        agents/graph.py's cmo_node runs a constitution check, and it does so
        after this function's caller already has its output, on a separate
        code path (the result is persisted on PipelineItem, not duplicated
        here). Real per-agent wiring is a candidate for a later phase.

        `run_id` (CompanyOS V3.1 Layer 4 — see core/telemetry.py) correlates
        every agent call from one pipeline run, enabling cost/latency-per-
        campaign queries (api/routes.py::get_campaign).
        """
        db = SessionLocal()
        try:
            evaluation = Evaluation(
                agent_id=agent_id,
                model_name=model_name,
                run_id=run_id,
                latency_ms=latency_ms,
                cost=output.get("cost", 0.0),
                confidence=output.get("confidence"),
                risk=output.get("risk"),
                schema_valid=is_schema_valid(output),
                constitution_violation_count=constitution_violation_count,
                requires_human_approval=requires_approval(output),
                vetoed=is_vetoed(output),
            )
            db.add(evaluation)
            db.commit()
            logger.info(
                "Evaluated %s (%s): confidence=%s latency_ms=%s cost=%s schema_valid=%s",
                agent_id, model_name, evaluation.confidence, latency_ms,
                evaluation.cost, evaluation.schema_valid,
            )
            return evaluation
        finally:
            db.close()

    def generate_benchmark(
        self,
        agent_id: str,
        model_name: str,
        window: timedelta = timedelta(days=1),
    ) -> Benchmark | None:
        """
        Aggregate recent Evaluation rows for one agent/model pair into a
        Benchmark snapshot. Returns None (persists nothing) if there are no
        evaluations in the window — an empty benchmark would be noise.
        """
        window_end = datetime.now(timezone.utc)
        window_start = window_end - window

        db = SessionLocal()
        try:
            rows = (
                db.query(Evaluation)
                .filter(
                    Evaluation.agent_id == agent_id,
                    Evaluation.model_name == model_name,
                    Evaluation.created_at >= window_start,
                    Evaluation.created_at <= window_end,
                )
                .all()
            )
            if not rows:
                logger.info("No evaluations for %s/%s in window — skipping benchmark.", agent_id, model_name)
                return None

            evaluation_dicts = [
                {
                    "confidence": r.confidence,
                    "latency_ms": r.latency_ms,
                    "cost": r.cost,
                    "schema_valid": r.schema_valid,
                    "vetoed": r.vetoed,
                }
                for r in rows
            ]
            aggregates = compute_benchmark_aggregates(evaluation_dicts)
            violation_rate = sum(1 for r in rows if r.constitution_violation_count > 0) / len(rows)

            benchmark = Benchmark(
                agent_id=agent_id,
                model_name=model_name,
                window_start=window_start,
                window_end=window_end,
                sample_count=aggregates["sample_count"],
                avg_confidence=aggregates["avg_confidence"],
                avg_latency_ms=aggregates["avg_latency_ms"],
                avg_cost=aggregates["avg_cost"],
                schema_valid_rate=aggregates["schema_valid_rate"],
                constitution_violation_rate=violation_rate,
                veto_rate=aggregates["veto_rate"],
            )
            db.add(benchmark)
            db.commit()
            logger.info(
                "Generated benchmark for %s/%s: %d samples, avg_confidence=%s",
                agent_id, model_name, benchmark.sample_count, benchmark.avg_confidence,
            )
            return benchmark
        finally:
            db.close()


evaluator = EvaluatorBrain()
