# webhook rules

Inbound and outbound webhook handling

## Business rules
- Always verify webhook signature before processing
- Respond 200 immediately — process async via queue
- Processing must be idempotent (same event ID = same outcome)
- Failed events must go to dead-letter queue, not silently dropped

## Common requirements
- Signature verification middleware
- Async job queue for processing
- Idempotency check by event ID
- Dead-letter queue with alerting
- Audit log for every webhook received and processed
- Retry logic for outbound webhooks

## Risk flags
- Synchronous processing blocks the webhook response → provider retries → duplicate processing
- Missing idempotency → duplicate side-effects on retry

## Required workflow
- 1. Receive webhook → verify signature → respond 200
- 2. Enqueue event payload to job queue
- 3. Worker: check idempotency → process → mark done
- 4. On failure: retry with backoff → DLQ after max retries

## Forbidden shortcuts
- Never process business logic in the webhook HTTP handler
- Never skip signature verification even in development

## Questions to ask
- Which queue system? (Redis, SQS, RabbitMQ)
- Max retry count and backoff strategy?
- Who gets alerted on DLQ events?

## Related domains
worker, payment, audit

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
