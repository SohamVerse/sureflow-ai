"""
Constitution — Company principles and brand guidelines enforcement layer.

Every agent output is validated against the Constitution before being finalized.
If a violation is detected, the output is flagged and sent to the Approval Center.

The Constitution covers:
  - Brand voice and messaging rules
  - Budget limits (per campaign, per agent action)
  - Legal / compliance constraints
  - Content policies (no competitor naming, no unverified claims)
  - Approval policies (what triggers human review)
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

from core.database import SessionLocal
from models.constitution import ConstitutionVersion


# ─── Default Company Constitution ─────────────────────────────────────────────

DEFAULT_CONSTITUTION = {
    "company_name": "CompanyOS",
    "brand_principles": [
        "Always lead with data and evidence",
        "Never make claims that cannot be substantiated",
        "Maintain a professional, confident, and empathetic tone",
        "Do not name competitors negatively or spread FUD",
        "Protect customer privacy at all times",
    ],
    "budget_limits": {
        "per_campaign_max_usd": 50000,
        "per_post_boost_max_usd": 500,
        "requires_ceo_above_usd": 10000,
        "requires_manager_above_usd": 2000,
    },
    "content_policies": [
        "No unverified statistical claims",
        "No direct competitor targeting without legal approval",
        "No urgency language that could be misleading",
        "All email subject lines must pass spam score check",
    ],
    "approval_policies": {
        "auto_approve_confidence_threshold": 75,
        "manager_approval_risk_levels": ["medium"],
        "ceo_approval_risk_levels": ["high", "critical"],
        "always_require_human_for": ["budget_spend", "public_statements", "legal_commitments"],
    },
    "legal_constraints": [
        "GDPR compliance required for all EU lead outreach",
        "CAN-SPAM compliance for all email campaigns",
        "No guarantees of specific ROI or returns",
    ],
}


# ─── Persistence (Immutable, Versioned Constitution) ──────────────────────────

def _load_active_constitution() -> dict:
    """
    Load the active constitution ruleset from Postgres, seeding version 1 from
    DEFAULT_CONSTITUTION if the table is empty. Falls back to DEFAULT_CONSTITUTION
    if the database isn't reachable yet (e.g. migrations not applied).
    """
    try:
        db = SessionLocal()
        try:
            active = (
                db.query(ConstitutionVersion)
                .filter(ConstitutionVersion.active == True)  # noqa: E712
                .order_by(ConstitutionVersion.version.desc())
                .first()
            )
            if active:
                return active.content
            content_json = json.dumps(DEFAULT_CONSTITUTION, sort_keys=True)
            db.add(ConstitutionVersion(
                version=1,
                sha256=hashlib.sha256(content_json.encode()).hexdigest(),
                content=DEFAULT_CONSTITUTION,
                approved_by="system",
                active=True,
            ))
            db.commit()
            return DEFAULT_CONSTITUTION
        finally:
            db.close()
    except Exception:
        return DEFAULT_CONSTITUTION


# ─── Constitution Violation ────────────────────────────────────────────────────

@dataclass
class ConstitutionViolation:
    rule: str
    severity: str       # "warning" | "blocker"
    details: str
    suggested_fix: str = ""


# ─── ConstitutionLayer ─────────────────────────────────────────────────────────

class ConstitutionLayer:
    """
    Validates any agent output against the company's constitution.
    
    Usage:
        constitution = ConstitutionLayer()
        violations = constitution.validate(output_dict, agent_id="CMO")
        if constitution.has_blockers(violations):
            # Escalate to human approval
    """

    def __init__(self, custom_constitution: Optional[dict] = None):
        self.rules = custom_constitution or _load_active_constitution()

    def validate(self, output: dict, agent_id: str = "") -> list[ConstitutionViolation]:
        """
        Run all validation checks on an agent output dict.
        Returns a list of violations (may be empty).
        """
        violations = []
        content_str = json.dumps(output).lower()

        # ── Brand Principles Check ──────────────────────────────────────────────
        forbidden_patterns = [
            ("guarantee", "Avoid guaranteed outcome language — replace with 'expected' or 'projected'"),
            ("100% sure", "Absolute certainty claims violate our evidence-first principle"),
            ("definitely will", "Definitive claims require verification before publishing"),
        ]
        for pattern, fix in forbidden_patterns:
            if pattern in content_str:
                violations.append(ConstitutionViolation(
                    rule="Brand Principles — No unverified absolute claims",
                    severity="warning",
                    details=f"Output contains restricted phrase: '{pattern}'",
                    suggested_fix=fix,
                ))

        # ── Budget Limit Check ──────────────────────────────────────────────────
        budget = self.rules.get("budget_limits", {})
        if "budget" in content_str or "spend" in content_str:
            # Heuristic: if output recommends spend, flag for manager review
            violations.append(ConstitutionViolation(
                rule="Budget Policy — Spend Recommendation Detected",
                severity="warning",
                details="Output includes budget/spend language. Manager approval may be required.",
                suggested_fix="Ensure recommended spend stays within per-campaign limit of $"
                              f"{budget.get('per_campaign_max_usd', 50000):,}",
            ))

        # ── Content Policy Check ────────────────────────────────────────────────
        for policy in self.rules.get("content_policies", []):
            # Check for spam trigger words in emails
            if agent_id == "EMAIL" and any(w in content_str for w in ["free!", "act now!", "limited time!!!"]):
                violations.append(ConstitutionViolation(
                    rule="Content Policy — Email Spam Risk",
                    severity="blocker",
                    details="Subject line or body may trigger spam filters",
                    suggested_fix="Remove exclamation-heavy urgency language",
                ))
                break

        # ── Legal Constraint Check ──────────────────────────────────────────────
        if "guarantee" in content_str and "roi" in content_str:
            violations.append(ConstitutionViolation(
                rule="Legal — ROI Guarantees Prohibited",
                severity="blocker",
                details="Output appears to guarantee ROI. This is a legal liability.",
                suggested_fix="Replace with 'clients typically see' or 'projected results suggest'",
            ))

        return violations

    def has_blockers(self, violations: list[ConstitutionViolation]) -> bool:
        """Return True if any violation is a hard blocker (prevents auto-approval)."""
        return any(v.severity == "blocker" for v in violations)

    def summarize(self, violations: list[ConstitutionViolation]) -> str:
        """Return a human-readable summary of all violations."""
        if not violations:
            return "✅ Constitution check passed — no violations detected."
        lines = [f"⚠️ {len(violations)} Constitution violation(s) detected:"]
        for v in violations:
            emoji = "🚫" if v.severity == "blocker" else "⚠️"
            lines.append(f"  {emoji} [{v.severity.upper()}] {v.rule}: {v.details}")
            if v.suggested_fix:
                lines.append(f"     → Fix: {v.suggested_fix}")
        return "\n".join(lines)

    def get_as_prompt_context(self) -> str:
        """Format the constitution as a compact text for injection into agent prompts."""
        rules = self.rules
        lines = ["=== COMPANY CONSTITUTION — YOU MUST COMPLY ==="]
        lines.append(f"Company: {rules.get('company_name', 'Your Company')}")
        lines.append("\nBrand Principles:")
        for p in rules.get("brand_principles", []):
            lines.append(f"  • {p}")
        lines.append("\nContent Policies:")
        for p in rules.get("content_policies", []):
            lines.append(f"  • {p}")
        lines.append("\nLegal Constraints:")
        for l in rules.get("legal_constraints", []):
            lines.append(f"  • {l}")
        lines.append("=== END CONSTITUTION ===")
        return "\n".join(lines)


# Singleton constitution instance
constitution = ConstitutionLayer()
