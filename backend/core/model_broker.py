"""
ModelBroker — Layer 2.5 of CompanyOS V3.1.

Responsibilities (per the V3.1 architecture spec):
  - Cost-aware Model Routing — agents are routed to the model configured for them
  - Fallbacks — if the primary model errors, transparently retry on a local model
  - Caching — in-process response cache (Redis was explicitly removed from V3.1)
  - Cost Governance — estimate USD cost per call from real token usage
"""
from __future__ import annotations
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_core.runnables import Runnable
from core.config import settings
from core.llm import get_llm

set_llm_cache(InMemoryCache())

# Approximate list-price USD per 1M tokens — a governance estimate, not exact billing.
# Ollama models are local/free and intentionally absent from this table.
MODEL_PRICING = {
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
}


def get_broker_llm(model_name: str, temperature: float = 0.5, format: str | None = None) -> Runnable:
    """
    Drop-in replacement for core.llm.get_llm() that adds automatic fallback to
    settings.FALLBACK_MODEL if the primary model errors (e.g. a deprecated/404
    model, rate limit, or network failure).
    """
    primary = get_llm(model_name, temperature, format)
    if model_name == settings.FALLBACK_MODEL:
        return primary
    fallback = get_llm(settings.FALLBACK_MODEL, temperature, format)
    return primary.with_fallbacks([fallback])


def estimate_cost(model_name: str, response) -> float:
    """Estimate USD cost of a single LLM call from its usage_metadata. Returns
    0.0 for Ollama/unknown models or responses with no usage_metadata."""
    usage = getattr(response, "usage_metadata", None)
    rates = MODEL_PRICING.get(model_name)
    if not usage or not rates:
        return 0.0
    return (
        (usage.get("input_tokens", 0) / 1_000_000) * rates["input"]
        + (usage.get("output_tokens", 0) / 1_000_000) * rates["output"]
    )
