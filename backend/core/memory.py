"""
MemoryStore — Multi-tier memory system for CompanyOS V2 agents.

Implements:
  - Episodic Memory:   Past task runs and their outcomes (stored in DB / in-memory)
  - Reflection Memory: Failures and lessons learned (prevents repeated mistakes)
  - Semantic Memory:   ChromaDB RAG (existing 01-voice, 02-icp, etc. collections)
  - Working Memory:    Current LangGraph AgentState (handled by the graph itself)
  - Procedural Memory: SOPs stored as documents in ChromaDB
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional

# In-process stores (replace with DB for production scale)
_episodic_store: dict[str, list[dict]] = {}   # agent_id -> list of episode dicts
_reflection_store: dict[str, list[dict]] = {}  # agent_id -> list of reflection dicts


# ─── MemoryStore ──────────────────────────────────────────────────────────────

class MemoryStore:
    """
    Unified interface to all memory tiers for a CompanyOS Brain.
    
    Episodic  — "What did I do last time?"
    Reflection— "What went wrong, and what did I learn?"
    Semantic  — ChromaDB RAG queries (delegated to rag.embeddings)
    """

    # ── Episodic Memory ────────────────────────────────────────────────────────

    def save_episodic(self, agent_id: str, task: str, output: dict) -> None:
        """Persist an episode (task run + result) for the given agent."""
        if agent_id not in _episodic_store:
            _episodic_store[agent_id] = []
        _episodic_store[agent_id].append({
            "task": task,
            "output_summary": _summarize_output(output),
            "confidence": output.get("confidence_score", 50),
            "risk": output.get("risk_level", "medium"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Cap at 50 episodes per agent
        _episodic_store[agent_id] = _episodic_store[agent_id][-50:]

    def get_episodic(self, agent_id: str, limit: int = 5) -> list[dict]:
        """Return the N most recent episodes for an agent."""
        episodes = _episodic_store.get(agent_id, [])
        return episodes[-limit:]

    # ── Reflection Memory ──────────────────────────────────────────────────────

    def save_reflection(self, agent_id: str, task: str, failure_reason: str, lesson: str) -> None:
        """
        Record a lesson learned from a failure or sub-optimal outcome.
        This feeds back into future executions to prevent repeated mistakes.
        """
        if agent_id not in _reflection_store:
            _reflection_store[agent_id] = []
        _reflection_store[agent_id].append({
            "task_context": task[:300],
            "failure_reason": failure_reason,
            "lesson": lesson,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        _reflection_store[agent_id] = _reflection_store[agent_id][-30:]

    def get_reflection(self, agent_id: str, current_task: str = "") -> str:
        """
        Return a formatted string of relevant lessons from past failures.
        Used to inject wisdom into agent prompts before execution.
        """
        reflections = _reflection_store.get(agent_id, [])
        if not reflections:
            return "No past failures on record. Proceed with full diligence."
        lines = ["LESSONS FROM PAST FAILURES — review before acting:"]
        for r in reflections[-5:]:
            lines.append(f"• [{r['timestamp'][:10]}] Context: {r['task_context']}")
            lines.append(f"  Failure: {r['failure_reason']}")
            lines.append(f"  Lesson:  {r['lesson']}")
        return "\n".join(lines)

    # ── Semantic Memory (RAG) ──────────────────────────────────────────────────

    def query_semantic(self, collection: str, query: str, n_results: int = 3) -> list[dict]:
        """
        Delegate to the existing ChromaDB RAG system.
        Returns list of {content, metadata} dicts.
        """
        try:
            from rag.embeddings import query_collection
            return query_collection(collection, query, n_results)
        except Exception:
            return []

    def get_voice_profile(self, query: str = "") -> str:
        results = self.query_semantic("01-voice", query or "brand voice tone style", n_results=3)
        return "\n".join(r["content"] for r in results) or "Professional, confident, data-driven tone."

    def get_icp(self, query: str = "") -> str:
        results = self.query_semantic("02-icp", query or "ideal customer profile", n_results=3)
        return "\n".join(r["content"] for r in results) or "B2B SaaS decision-makers and founders."

    def get_content_pillars(self, query: str = "") -> str:
        results = self.query_semantic("04-content-pillars", query, n_results=3)
        return "\n".join(r["content"] for r in results) or "Thought leadership, product demos, case studies."

    def get_research_vault(self, query: str = "") -> str:
        results = self.query_semantic("05-research", query, n_results=4)
        return "\n".join(r["content"] for r in results) or "No existing research data."

    def get_what_works(self, query: str = "") -> str:
        results = self.query_semantic("06-what-works", query, n_results=2)
        return "\n".join(r["content"] for r in results) or "No performance history available."

    # ── Memory Summary ─────────────────────────────────────────────────────────

    def get_memory_summary(self, agent_id: str) -> dict:
        """Return a structured summary of all memory tiers for an agent."""
        return {
            "episodic_count": len(_episodic_store.get(agent_id, [])),
            "reflection_count": len(_reflection_store.get(agent_id, [])),
            "recent_episodes": self.get_episodic(agent_id, limit=3),
            "recent_reflections": _reflection_store.get(agent_id, [])[-3:],
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _summarize_output(output: dict) -> str:
    """Create a short summary string from a BrainOutput dict for storage."""
    parts = []
    if r := output.get("recommendation"):
        parts.append(f"Rec: {str(r)[:100]}")
    if c := output.get("confidence_score"):
        parts.append(f"Confidence: {c}%")
    if r := output.get("risk_level"):
        parts.append(f"Risk: {r}")
    return " | ".join(parts) or json.dumps(output)[:200]
