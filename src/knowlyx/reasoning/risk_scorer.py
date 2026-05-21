"""Scores risk and produces an AI decision: proceed / warn / ask / reject."""

from __future__ import annotations

from knowlyx.models.schema import (
    AIDecision,
    ImpactAnalysis,
    IntentAnalysis,
    RiskAssessment,
    RiskLevel,
    ScanResult,
)

_CRITICAL_DOMAINS = {"payment", "auth", "webhook"}
_HIGH_DOMAINS = {"order", "user", "audit", "worker"}

_HIGH_RISK_ACTIONS = {"delete", "migrate", "refactor"}
_DANGEROUS_KEYWORDS = [
    "drop table", "truncate", "delete from", "force", "--no-verify",
    "rm -rf", "production", "prod", "live", "bypass", "skip",
]


class RiskScorer:
    def __init__(self, scan: ScanResult) -> None:
        self.scan = scan

    def score(self, intent: IntentAnalysis, impact: ImpactAnalysis) -> RiskAssessment:
        reasons: list[str] = []
        warnings: list[str] = []
        workflow: list[str] = []
        score = 0

        # --- action risk ---
        if intent.detected_action in _HIGH_RISK_ACTIONS:
            score += 2
            reasons.append(f"Action '{intent.detected_action}' is inherently risky")

        # --- domain criticality ---
        if intent.detected_domain in _CRITICAL_DOMAINS:
            score += 3
            reasons.append(f"Domain '{intent.detected_domain}' is marked CRITICAL")
        elif intent.detected_domain in _HIGH_DOMAINS:
            score += 2
            reasons.append(f"Domain '{intent.detected_domain}' is HIGH impact")

        # --- cascade breadth ---
        n_domains = len(impact.affected_domains)
        if n_domains >= 4:
            score += 2
            reasons.append(f"Change cascades across {n_domains} domains")
        elif n_domains >= 2:
            score += 1

        # --- dangerous keywords in request ---
        request_lower = intent.raw_request.lower()
        for kw in _DANGEROUS_KEYWORDS:
            if kw in request_lower:
                score += 3
                reasons.append(f"Request contains dangerous keyword: '{kw}'")
                break

        # --- generated files ---
        if self.scan.api_clients and intent.detected_domain in _CRITICAL_DOMAINS:
            warnings.append("Swagger/OpenAPI changes require client regeneration — do not skip this step")
            workflow.extend([
                "1. Update backend DTO / API contract",
                "2. Regenerate Swagger spec",
                "3. Rebuild generated client",
                "4. Update all call sites to new client",
            ])

        # --- forbidden pattern violations ---
        if self.scan.forbidden_patterns:
            warnings.append("Enforce forbidden patterns: " + " | ".join(self.scan.forbidden_patterns[:2]))

        # --- clarification needed ---
        if intent.requires_clarification:
            score += 1
            warnings.extend(f"Clarification needed: {q}" for q in intent.clarification_questions)

        # --- cascade risks ---
        warnings.extend(impact.cascade_risks[:3])

        # --- decision ---
        level, decision = self._decide(score)

        return RiskAssessment(
            level=level,
            reasons=reasons,
            decision=decision,
            warnings=warnings,
            required_workflow=workflow,
        )

    def _decide(self, score: int) -> tuple[RiskLevel, AIDecision]:
        if score >= 7:
            return RiskLevel.CRITICAL, AIDecision.REJECT
        if score >= 5:
            return RiskLevel.HIGH, AIDecision.ASK
        if score >= 3:
            return RiskLevel.MEDIUM, AIDecision.WARN
        return RiskLevel.LOW, AIDecision.PROCEED
