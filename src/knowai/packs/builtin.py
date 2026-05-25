"""
Built-in cognition packs — domain knowledge that AI must apply
even when the codebase doesn't make it explicit.

These represent hard-won patterns from production systems.
Teams can override or extend via memory store.
"""

from __future__ import annotations

from knowai.packs.schema import CognitionPack

BUILTIN_PACKS: dict[str, CognitionPack] = {
    "auth": CognitionPack(
        domain="auth",
        description="Authentication and authorization domain",
        business_rules=[
            "Passwords must never be stored in plain text",
            "JWT tokens must have expiration",
            "Failed login attempts must be rate-limited (max 5/15min is a safe default)",
            "Session invalidation must be possible (logout from all devices)",
            "Sensitive auth events must be audit logged",
        ],
        common_requirements=[
            "Register / Login / Logout flows",
            "Token refresh mechanism",
            "Password reset via email/OTP",
            "Rate limiting on auth endpoints",
            "Brute force protection",
            "Audit logging for login/logout/failed attempts",
            "Notification for suspicious login (new device/location)",
        ],
        risk_flags=[
            "Changing token signing key invalidates all active sessions",
            "Changing session strategy may log out all users",
            "Removing auth middleware can expose protected routes",
        ],
        required_workflow=[
            "1. Define auth flow (register → verify → login → refresh → logout)",
            "2. Choose token strategy (JWT / session / OAuth)",
            "3. Implement rate limiting before exposing endpoints",
            "4. Add audit logging",
            "5. Test brute force scenarios",
            "6. Security review before production",
        ],
        forbidden_shortcuts=[
            "Never disable rate limiting 'temporarily'",
            "Never log raw passwords or tokens",
            "Never use MD5/SHA1 for password hashing — use bcrypt/argon2",
        ],
        related_domains=["user", "audit", "notification"],
        questions_to_ask=[
            "Which token strategy: JWT, session, or OAuth provider?",
            "What is the token expiry window?",
            "Which notification provider for login alerts?",
            "Is 2FA/MFA required?",
        ],
    ),

    "otp": CognitionPack(
        domain="otp",
        description="One-time password flows (SMS/email verification)",
        business_rules=[
            "OTP must expire (5–10 minutes is standard)",
            "OTP must be single-use — invalidate on first use",
            "Max OTP retry limit before lock (3–5 attempts)",
            "Resend must have cool-down (60 seconds minimum)",
            "OTP must not be logged in plain text",
        ],
        common_requirements=[
            "Generate cryptographically random OTP (6 digits / UUID token)",
            "Store hashed OTP with expiry timestamp",
            "Resend flow with cool-down enforcement",
            "Lock account/IP after max retries",
            "Notification provider integration (SMS or email)",
            "Audit log OTP requests and verification attempts",
        ],
        risk_flags=[
            "OTP sent over SMS can be intercepted (SIM swap) — consider authenticator app for sensitive ops",
            "Not expiring OTPs is a critical security flaw",
            "Predictable OTPs (sequential, timestamp-based) are exploitable",
        ],
        required_workflow=[
            "1. Generate OTP → hash → store with expiry",
            "2. Send OTP via notification provider",
            "3. Verify: check hash + expiry + retry count",
            "4. Invalidate on success; increment counter on failure",
            "5. Lock after max retries",
        ],
        forbidden_shortcuts=[
            "Never store OTP in plain text",
            "Never skip expiry check",
            "Never allow unlimited retries",
        ],
        related_domains=["auth", "notification", "audit"],
        questions_to_ask=[
            "Notification channel: SMS, email, or authenticator app?",
            "OTP length and expiry window?",
            "Max retry count before lock?",
            "Should lock be per-user or per-IP?",
        ],
    ),

    "payment": CognitionPack(
        domain="payment",
        description="Payment processing domain",
        business_rules=[
            "Every payment operation must be idempotent (idempotency key)",
            "Payment status must be a finite state machine: pending → processing → success | failed | refunded",
            "Never trust client-side payment amount — always verify server-side",
            "Webhook signature must be verified before processing",
            "Double-charge must be impossible",
        ],
        common_requirements=[
            "Idempotency key on payment creation",
            "Webhook handler: verify signature → queue async processing → respond 200 immediately",
            "Payment status sync (polling or webhook)",
            "Refund flow with audit trail",
            "Dead-letter queue for failed webhook processing",
            "Audit log every payment lifecycle event",
            "Retry logic with exponential backoff for provider calls",
        ],
        risk_flags=[
            "Changing payment DTO requires Swagger regeneration and client rebuild",
            "Webhook retry without idempotency → duplicate charges",
            "Async status updates can cause race conditions on order state",
            "Provider API changes can silently break payment flow",
        ],
        required_workflow=[
            "1. Update backend DTO / API contract",
            "2. Regenerate Swagger spec",
            "3. Rebuild generated client",
            "4. Update webhook handler if status codes changed",
            "5. Test in provider sandbox before production",
            "6. Monitor retry queue after deploy",
        ],
        forbidden_shortcuts=[
            "Never process webhooks synchronously (always async via queue)",
            "Never skip webhook signature verification",
            "Never expose raw provider errors to frontend",
            "Never trust client-provided payment amount",
        ],
        related_domains=["webhook", "worker", "audit", "notification", "order"],
        questions_to_ask=[
            "Which payment provider? (Stripe, Omise, PromptPay, etc.)",
            "Is refund flow required?",
            "What happens on provider downtime — queue or reject?",
            "Is partial payment supported?",
        ],
    ),

    "webhook": CognitionPack(
        domain="webhook",
        description="Inbound and outbound webhook handling",
        business_rules=[
            "Always verify webhook signature before processing",
            "Respond 200 immediately — process async via queue",
            "Processing must be idempotent (same event ID = same outcome)",
            "Failed events must go to dead-letter queue, not silently dropped",
        ],
        common_requirements=[
            "Signature verification middleware",
            "Async job queue for processing",
            "Idempotency check by event ID",
            "Dead-letter queue with alerting",
            "Audit log for every webhook received and processed",
            "Retry logic for outbound webhooks",
        ],
        risk_flags=[
            "Synchronous processing blocks the webhook response → provider retries → duplicate processing",
            "Missing idempotency → duplicate side-effects on retry",
        ],
        required_workflow=[
            "1. Receive webhook → verify signature → respond 200",
            "2. Enqueue event payload to job queue",
            "3. Worker: check idempotency → process → mark done",
            "4. On failure: retry with backoff → DLQ after max retries",
        ],
        forbidden_shortcuts=[
            "Never process business logic in the webhook HTTP handler",
            "Never skip signature verification even in development",
        ],
        related_domains=["worker", "payment", "audit"],
        questions_to_ask=[
            "Which queue system? (Redis, SQS, RabbitMQ)",
            "Max retry count and backoff strategy?",
            "Who gets alerted on DLQ events?",
        ],
    ),

    "order": CognitionPack(
        domain="order",
        description="Order lifecycle management",
        business_rules=[
            "Order status must be a state machine — no backward transitions (e.g. completed → pending is invalid)",
            "Stock must be reserved (not deducted) at order creation",
            "Payment must be confirmed before stock deduction",
            "Cancellation must release reserved stock",
        ],
        common_requirements=[
            "Order state machine: draft → confirmed → paid → shipped → completed | cancelled",
            "Stock reservation on order creation",
            "Payment flow trigger on order confirmation",
            "Inventory deduction on payment success",
            "Notification at each status transition",
            "Audit log for every order event",
        ],
        risk_flags=[
            "Race condition on stock reservation under high concurrency",
            "Payment success webhook may arrive before order status update",
            "Cancellation after shipment requires manual intervention",
        ],
        required_workflow=[
            "1. Validate cart and stock availability",
            "2. Create order (reserved stock, status=draft)",
            "3. Initiate payment → status=pending_payment",
            "4. On payment success webhook: deduct stock, status=paid",
            "5. Trigger shipping, notify user",
        ],
        related_domains=["payment", "inventory", "notification", "shipping", "audit"],
        questions_to_ask=[
            "Is partial order fulfillment supported?",
            "What happens if stock runs out between reservation and payment?",
            "Can orders be split across multiple shipments?",
        ],
    ),

    "notification": CognitionPack(
        domain="notification",
        description="Multi-channel notification system",
        business_rules=[
            "Notifications must be async — never block main flow",
            "User notification preferences must be respected",
            "Failed notifications must be retried, not silently dropped",
            "Notification content must not contain sensitive data in plain text",
        ],
        common_requirements=[
            "Multi-channel support (email, SMS, push, in-app)",
            "Template system for notification content",
            "User preference management (opt-out per channel/type)",
            "Retry logic for failed deliveries",
            "Delivery tracking and audit log",
        ],
        risk_flags=[
            "Notification provider downtime can cascade if not async",
            "Sending duplicate notifications on retry without idempotency",
        ],
        required_workflow=[
            "1. Trigger notification event → enqueue",
            "2. Worker: load user preferences → select channel → render template",
            "3. Send via provider → log delivery status",
            "4. Retry on failure",
        ],
        forbidden_shortcuts=[
            "Never send notifications synchronously in request flow",
            "Never hardcode notification content — use templates",
        ],
        related_domains=["worker", "user", "audit"],
        questions_to_ask=[
            "Which providers? (SendGrid, Twilio, FCM, etc.)",
            "Does user have per-channel opt-out preference?",
            "Is notification history visible to user?",
        ],
    ),

    "worker": CognitionPack(
        domain="worker",
        description="Background job and queue processing",
        business_rules=[
            "Jobs must be idempotent — safe to run multiple times",
            "Max retry count must be defined — never infinite retry",
            "Failed jobs after max retries must go to DLQ",
            "Long-running jobs must have timeout",
        ],
        common_requirements=[
            "Job idempotency by job ID",
            "Retry with exponential backoff",
            "Dead-letter queue",
            "Job monitoring and alerting",
            "Graceful shutdown handling",
        ],
        risk_flags=[
            "Non-idempotent jobs on retry can cause data corruption",
            "Unbounded retry → infinite loop on persistent errors",
            "No timeout → job holds queue slot forever",
        ],
        required_workflow=[
            "1. Define job schema with idempotency key",
            "2. Implement retry policy (max N, backoff strategy)",
            "3. Add DLQ routing",
            "4. Add monitoring hooks",
            "5. Test failure and retry scenarios",
        ],
        forbidden_shortcuts=[
            "Never write non-idempotent job logic",
            "Never skip DLQ setup",
        ],
        related_domains=["payment", "webhook", "notification"],
        questions_to_ask=[
            "Which queue backend? (Redis/BullMQ, Celery, SQS)",
            "Max retry count and backoff multiplier?",
            "Who is alerted on DLQ events?",
        ],
    ),
}


def get_pack(domain: str) -> CognitionPack | None:
    return BUILTIN_PACKS.get(domain.lower())


def get_packs_for_domains(domains: list[str]) -> list[CognitionPack]:
    packs: list[CognitionPack] = []
    seen: set[str] = set()
    for d in domains:
        pack = get_pack(d)
        if pack and d not in seen:
            seen.add(d)
            packs.append(pack)
    return packs
