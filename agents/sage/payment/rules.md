# payment rules

Payment processing domain

## Business rules
- Every payment operation must be idempotent (idempotency key)
- Payment status must be a finite state machine: pending → processing → success | failed | refunded
- Never trust client-side payment amount — always verify server-side
- Webhook signature must be verified before processing
- Double-charge must be impossible

## Common requirements
- Idempotency key on payment creation
- Webhook handler: verify signature → queue async processing → respond 200 immediately
- Payment status sync (polling or webhook)
- Refund flow with audit trail
- Dead-letter queue for failed webhook processing
- Audit log every payment lifecycle event
- Retry logic with exponential backoff for provider calls

## Risk flags
- Changing payment DTO requires Swagger regeneration and client rebuild
- Webhook retry without idempotency → duplicate charges
- Async status updates can cause race conditions on order state
- Provider API changes can silently break payment flow

## Required workflow
- 1. Update backend DTO / API contract
- 2. Regenerate Swagger spec
- 3. Rebuild generated client
- 4. Update webhook handler if status codes changed
- 5. Test in provider sandbox before production
- 6. Monitor retry queue after deploy

## Forbidden shortcuts
- Never process webhooks synchronously (always async via queue)
- Never skip webhook signature verification
- Never expose raw provider errors to frontend
- Never trust client-provided payment amount

## Questions to ask
- Which payment provider? (Stripe, Omise, PromptPay, etc.)
- Is refund flow required?
- What happens on provider downtime — queue or reject?
- Is partial payment supported?

## Related domains
webhook, worker, audit, notification, order

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
