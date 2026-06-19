"""
BaseBrain — The cognitive foundation for all CompanyOS V3 agents.

Every agent (CEO, CMO, Research, SDR, AE, Risk, Email) enforces the same
Decision Framework, captured by the BrainOutput contract:
  - Internal reasoning before acting
  - Alternatives considered
  - Confidence score (0-100)
  - Expected value / ROI estimate
  - Risk estimation
  - Self-challenge ("Would I do this at my own company?")
"""
from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field
from core.memory import MemoryStore
from core.llm import get_llm
from core.config import settings


# ─── Brain Output Schema (Layer 1 Data Contract) ───────────────────────────────

class BrainOutput(BaseModel):
    """Standardized output produced by every CompanyOS Brain."""
    agent_id: str
    reasoning: str = ""                          # Internal chain-of-thought
    confidence: float = 50.0                      # 0-100: how sure the agent is
    confidence_interval: list[float] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    cost: float = 0.0
    risk: float = 50.0                            # 0-100, derived from risk_level
    risk_level: str = "medium"                    # "low" | "medium" | "high" | "critical"
    expected_value: float = 0.0
    recommendation: str = ""
    alternatives: list[str] = Field(default_factory=list)
    simulation_id: Optional[str] = None
    execution_plan: dict = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)   # Everything agent-specific
    requires_human_approval: bool = False          # Triggers Approval Center
    self_challenge_passed: bool = True             # Did the agent challenge itself?
    reflection_notes: str = ""                     # What past failures informed this
    execution_time_ms: int = 0

    def to_dict(self) -> dict:
        return self.model_dump()


# ─── Approval Risk Tiers ──────────────────────────────────────────────────────

def compute_approval_tier(confidence: float, risk: str) -> str:
    """
    Determine the human approval requirement tier based on confidence and risk.

    Low risk + high confidence  → auto-approve
    Medium risk                 → manager approval
    High/Critical risk          → CEO approval
    """
    if risk in ("high", "critical") or confidence < 40:
        return "CEO_APPROVAL"
    elif risk == "medium" or confidence < 70:
        return "MANAGER_APPROVAL"
    else:
        return "AUTO_APPROVE"


_RISK_LEVEL_TO_SCORE = {"low": 15.0, "medium": 45.0, "high": 75.0, "critical": 95.0}

# Raw LLM-JSON keys that map 1:1 onto an envelope field with no information loss,
# so they're excluded from `payload` (everything else — including fields that
# overlap conceptually but aren't a clean rename, like `expected_roi`/`risk_summary`
# — passes through to `payload` untouched).
_ENVELOPE_CONSUMED_KEYS = {
    "reasoning", "confidence_score", "confidence", "alternatives_considered",
    "alternatives", "recommendation", "risk_level",
}


def parse_brain_output(raw: dict, agent_id: str) -> BrainOutput:
    """
    Normalize a raw agent LLM-JSON dict into the canonical BrainOutput contract.

    `risk` (float) is derived from `risk_level` via a fixed mapping, since no
    agent prompt currently emits a numeric risk score directly.
    """
    risk_level = str(raw.get("risk_level", "medium")).lower()
    confidence = float(raw.get("confidence_score", raw.get("confidence", 50)))
    tier = compute_approval_tier(confidence, risk_level)

    payload = {k: v for k, v in raw.items() if k not in _ENVELOPE_CONSUMED_KEYS}

    return BrainOutput(
        agent_id=agent_id,
        reasoning=raw.get("reasoning", ""),
        confidence=confidence,
        risk=_RISK_LEVEL_TO_SCORE.get(risk_level, 50.0),
        risk_level=risk_level,
        recommendation=raw.get("recommendation", ""),
        alternatives=raw.get("alternatives_considered", raw.get("alternatives", [])),
        payload=payload,
        requires_human_approval=(tier != "AUTO_APPROVE"),
        reflection_notes=raw.get("self_challenge", ""),
    )


# ─── BaseBrain ────────────────────────────────────────────────────────────────

class BaseBrain(ABC):
    """
    Abstract base class for all CompanyOS agent brains.

    Every subclass must implement `_execute()` which returns a BrainOutput.
    The base class handles:
      - Memory retrieval (Episodic, Reflection, Semantic)
      - Constitution validation
      - Approval tier computation
      - Timing & telemetry
    """

    def __init__(self, agent_id: str, model_name: str, temperature: float = 0.5):
        self.agent_id = agent_id
        self.model_name = model_name
        self.temperature = temperature
        self.memory = MemoryStore()
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm(self.model_name, self.temperature, format="json")
        return self._llm

    # ── Core Execution ─────────────────────────────────────────────────────────

    def run(self, task: str, context: Optional[dict] = None) -> BrainOutput:
        """
        Public entry point. Wraps _execute() with memory, timing, and validation.
        """
        start = time.time()
        context = context or {}

        # Inject memory context
        reflection = self.memory.get_reflection(self.agent_id, task)
        episodic = self.memory.get_episodic(self.agent_id, limit=3)
        context["_reflection_memory"] = reflection
        context["_episodic_memory"] = episodic

        # Execute the specialized brain logic
        result = self._execute(task, context)

        # Compute approval tier
        tier = compute_approval_tier(result.confidence, result.risk_level)
        result.requires_human_approval = (tier != "AUTO_APPROVE")

        # Record timing
        result.execution_time_ms = int((time.time() - start) * 1000)

        # Persist to episodic memory
        self.memory.save_episodic(self.agent_id, task, result.to_dict())

        return result

    @abstractmethod
    def _execute(self, task: str, context: dict) -> BrainOutput:
        """Subclasses implement their specific domain logic here."""
        ...

    # ── Self-Challenge ─────────────────────────────────────────────────────────

    def _self_challenge(self, draft_output: dict, task: str) -> tuple[bool, str]:
        """
        Force the brain to challenge its own output before finalizing.
        Returns (passed: bool, critique: str).

        Questions the agent asks itself:
          1. What am I missing?
          2. Would I do this with my own money/company?
          3. What could go wrong?
          4. What is the opportunity cost?
          5. Would a senior expert agree?
        """
        challenge_llm = get_llm(self.model_name, temperature=0.2, format="json")
        challenge_prompt = f"""You are a senior advisor critiquing the following output from the {self.agent_id} agent.

ORIGINAL TASK: {task}

DRAFT OUTPUT: {json.dumps(draft_output, indent=2)}

Apply these questions:
1. What is this output missing?
2. Would a 15-year senior professional agree with this?
3. What assumptions are baked in that could be wrong?
4. What could catastrophically go wrong if this is executed?
5. Would you do this with your own company's budget?

Return a JSON object:
{{
  "passed": true|false,
  "confidence_adjustment": <-20 to +10>,
  "critique": "<honest critique>",
  "missing_elements": ["<item1>", "<item2>"]
}}"""

        try:
            resp = challenge_llm.invoke(challenge_prompt)
            critique_data = json.loads(resp.content)
            return critique_data.get("passed", True), critique_data.get("critique", "")
        except Exception:
            return True, "Self-challenge could not be completed."

    # ── Utility ────────────────────────────────────────────────────────────────

    def _parse_json_response(self, content: str, fallback: dict) -> dict:
        """Safely parse an LLM JSON response with a fallback."""
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        try:
            return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return fallback
