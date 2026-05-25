# Cognition Packs

Built-in domain knowledge bundles. When AI works on a domain, Knowai injects the relevant pack into the cognition report — so the AI knows the rules even if your codebase doesn't spell them out.

## What's in a pack

Each pack has six sections:

- **business_rules** — what must not be violated
- **common_requirements** — what every implementation needs
- **risk_flags** — known danger zones
- **required_workflow** — order of operations
- **forbidden_shortcuts** — common bad patterns to avoid
- **questions_to_ask** — clarifications to ask before coding

## Available packs

| Domain | Example rule |
|---|---|
| `auth` | Passwords must never be plain text. JWT must have expiration. Rate limit required. |
| `otp` | OTP must expire (5-10 min), single-use, max retry before lockout. |
| `payment` | Idempotency key required. Never trust client-side amount. Webhook signature must be verified. |
| `webhook` | Respond 200 immediately, process async. Idempotency by event ID. |
| `order` | State machine (no backward transitions). Reserve stock before payment. |
| `notification` | Always async. Respect user preferences. Retry on failure. |
| `worker` | Jobs must be idempotent. Max retry defined. DLQ required. |

## Inspect a pack

```bash
knowai pack auth
```

Sample output:

```text
Cognition Pack: auth

Business Rules:
  • Passwords must never be stored in plain text
  • JWT tokens must have expiration
  • Rate limiting required on all auth endpoints

Common Requirements:
  • Audit log for every auth event
  • Account lockout after N failed attempts
  • Secure session storage

Risk Flags:
  ⚠ Brute force attempts
  ⚠ Token replay
  ⚠ Session fixation

Forbidden Shortcuts:
  ✗ Skipping rate limits "just for now"
  ✗ Reusing OTP tokens
  ✗ Trusting client-provided user IDs

Questions to clarify:
  ? Per-user or per-IP rate limit?
  ? Lockout duration?
  ? Where to log audit events?
```

## Use via MCP

```text
get_cognition_pack("auth")  → returns the pack as JSON
analyze_intent("add login") → auto-injects relevant packs
```

## Team-specific packs (planned)

Phase 4 will allow custom packs at `~/.knowai/workspaces/<name>/packs/` so teams can codify their own conventions. For now, use [`memory decide`](cli.md#memory-decide) to record team-specific rules.

## Contributing a pack

Built-in packs live in [src/knowai/packs/builtin.py](../src/knowai/packs/builtin.py). Open a PR adding a new `CognitionPack(...)` entry + a test in `tests/test_packs.py`.

Strong packs cover domains that have well-known industry pitfalls — for example: `search`, `cache`, `feature_flag`, `analytics`, `gdpr`, `pci`.
