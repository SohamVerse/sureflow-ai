"""
OpenTelemetry setup — CompanyOS V3.1 Layer 4 Observability.

Traces export via OTLP to Jaeger (docker-compose service `jaeger`, ports
4317/4318). Metrics export via the OTel Prometheus bridge, scraped by the
`prometheus` docker-compose service from this app's /metrics endpoint.

See the Phase 6 plan for what's deliberately *not* built here (MCP
reliability, agent drift detection, confidence calibration) — those need real
signals this system doesn't have yet; see evaluation/evaluator.py and
meta_learning/brain.py for the same principle applied in earlier phases.
"""
from __future__ import annotations
import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app

logger = logging.getLogger("companyos.telemetry")

SERVICE_NAME = "companyos-backend"
OTLP_ENDPOINT = "localhost:4317"

_tracer: trace.Tracer | None = None


def setup_telemetry(app) -> None:
    """
    Configure tracing + metrics and instrument the FastAPI app. Call once
    from main.py at startup. Safe to call even if Jaeger is unreachable —
    the OTLP exporter retries in the background and never blocks requests.
    """
    resource = Resource.create({"service.name": SERVICE_NAME})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    global _tracer
    _tracer = trace.get_tracer(SERVICE_NAME)

    prometheus_reader = PrometheusMetricReader()
    metrics_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
    from opentelemetry import metrics
    metrics.set_meter_provider(metrics_provider)

    FastAPIInstrumentor.instrument_app(app)
    app.mount("/metrics", make_asgi_app())

    logger.info(f"OpenTelemetry configured: traces -> {OTLP_ENDPOINT}, metrics -> /metrics")


def get_tracer() -> trace.Tracer:
    """Returns the configured tracer, or a no-op tracer if setup_telemetry() hasn't run
    (e.g. one-off scripts) — span calls become harmless no-ops rather than crashing."""
    return _tracer or trace.get_tracer(SERVICE_NAME)
