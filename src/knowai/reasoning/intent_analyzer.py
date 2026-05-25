"""
Analyzes user intent from a natural language request.
Rule-based — no LLM call required. Claude receives this output via MCP
and uses it as structured context before reasoning further.
"""

from __future__ import annotations

import re

from knowai.models.schema import IntentAnalysis, ScanResult

_ACTION_PATTERNS: list[tuple[str, str]] = [
    (r"\b(add|create|implement|build|introduce)\b", "add"),
    (r"\b(fix|resolve|repair|debug|patch)\b", "fix"),
    (r"\b(update|change|modify|edit|refactor)\b", "modify"),
    (r"\b(delete|remove|drop|clean up)\b", "delete"),
    (r"\b(refactor|restructure|rewrite|clean)\b", "refactor"),
    (r"\b(migrate|upgrade|update)\b", "migrate"),
]

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "auth": ["login", "logout", "otp", "token", "jwt", "session", "password", "register", "2fa", "mfa", "oauth"],
    "payment": ["payment", "pay", "invoice", "billing", "charge", "refund", "wallet", "scan", "qr", "promptpay"],
    "user": ["user", "profile", "account", "member", "customer"],
    "order": ["order", "cart", "checkout", "purchase", "booking"],
    "notification": ["notification", "email", "sms", "push", "alert", "remind"],
    "webhook": ["webhook", "callback", "event", "trigger"],
    "audit": ["audit", "log", "history", "trail", "track"],
    "inventory": ["stock", "inventory", "warehouse", "product"],
    "shipping": ["shipping", "delivery", "courier", "logistics"],
    "report": ["report", "dashboard", "analytics", "metric", "chart"],
    "admin": ["admin", "backoffice", "management", "cms"],
    "worker": ["worker", "queue", "job", "cron", "task", "background"],
    "search": ["search", "filter", "query", "elasticsearch"],
}

_INFERRED_REQUIREMENTS: dict[str, list[str]] = {
    "auth": [
        "Implement authentication flow (register / login / logout)",
        "Handle token expiration and refresh",
        "Add rate limiting to prevent brute force",
        "Audit log all auth events",
        "Consider notification for login alerts",
    ],
    "otp": [
        "OTP must expire (typically 5–10 min)",
        "Implement resend OTP with cool-down",
        "Enforce max retry limit before lock",
        "Audit log OTP attempts",
        "Select notification provider (SMS/email)",
    ],
    "payment": [
        "Prevent duplicate payment (idempotency key)",
        "Handle payment status: pending / success / failed / refunded",
        "Webhook must handle retries and verify signature",
        "Audit log every payment event",
        "Update order/inventory on success",
        "Consider worker for async processing",
    ],
    "webhook": [
        "Verify webhook signature",
        "Respond 200 immediately, process async via queue",
        "Handle idempotency for duplicate events",
        "Dead-letter queue for failed processing",
    ],
    "worker": [
        "Implement retry logic with backoff",
        "Define max retry count and failure behavior",
        "Add monitoring/alerting for failed jobs",
    ],
    "order": [
        "Validate stock before order creation",
        "Trigger payment flow",
        "Send order confirmation notification",
        "Audit log order lifecycle",
    ],
}


class IntentAnalyzer:
    def __init__(self, scan: ScanResult) -> None:
        self.scan = scan

    def analyze(self, request: str) -> IntentAnalysis:
        request_lower = request.lower()
        action = self._detect_action(request_lower)
        domain = self._detect_domain(request_lower)
        affected = self._detect_affected_areas(request_lower, domain)
        requirements = self._infer_requirements(request_lower, domain)
        needs_clarification, questions = self._check_clarification(request_lower, domain, action)

        return IntentAnalysis(
            raw_request=request,
            detected_domain=domain,
            detected_action=action,
            affected_areas=affected,
            inferred_requirements=requirements,
            requires_clarification=needs_clarification,
            clarification_questions=questions,
        )

    def _detect_action(self, text: str) -> str:
        for pattern, action in _ACTION_PATTERNS:
            if re.search(pattern, text):
                return action
        return "unknown"

    def _detect_domain(self, text: str) -> str:
        scores: dict[str, int] = {}
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score:
                scores[domain] = score
        if not scores:
            # fall back: check against scanned domains
            for domain in self.scan.domains:
                if domain in text:
                    return domain
            return "general"
        return max(scores, key=lambda k: scores[k])

    def _detect_affected_areas(self, text: str, primary_domain: str) -> list[str]:
        areas: list[str] = [primary_domain] if primary_domain != "general" else []
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            if domain != primary_domain and any(kw in text for kw in keywords):
                areas.append(domain)
        # always include audit if changing critical domain
        if primary_domain in ("payment", "auth", "order") and "audit" not in areas:
            areas.append("audit")
        return list(dict.fromkeys(areas))  # preserve order, dedupe

    def _infer_requirements(self, text: str, domain: str) -> list[str]:
        reqs: list[str] = []
        # domain-level requirements
        reqs.extend(_INFERRED_REQUIREMENTS.get(domain, []))
        # keyword-level extra requirements
        for key, extra in _INFERRED_REQUIREMENTS.items():
            if key != domain and key in text:
                reqs.extend(extra)
        return list(dict.fromkeys(reqs))

    def _check_clarification(self, text: str, domain: str, action: str) -> tuple[bool, list[str]]:
        questions: list[str] = []
        if domain == "general" and action == "unknown":
            questions.append("Which domain or feature does this request relate to?")
        if action in ("delete", "refactor") and not any(w in text for w in ["confirm", "safe", "backup"]):
            questions.append("Is this a safe-to-run operation in production? Any rollback plan?")
        if domain == "payment" and action in ("modify", "fix") and "test" not in text:
            questions.append("Has this been verified against the payment provider sandbox?")
        return bool(questions), questions
