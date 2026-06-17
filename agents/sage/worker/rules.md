# worker rules

Background job and queue processing

## Business rules
- Jobs must be idempotent — safe to run multiple times
- Max retry count must be defined — never infinite retry
- Failed jobs after max retries must go to DLQ
- Long-running jobs must have timeout

## Common requirements
- Job idempotency by job ID
- Retry with exponential backoff
- Dead-letter queue
- Job monitoring and alerting
- Graceful shutdown handling

## Risk flags
- Non-idempotent jobs on retry can cause data corruption
- Unbounded retry → infinite loop on persistent errors
- No timeout → job holds queue slot forever

## Required workflow
- 1. Define job schema with idempotency key
- 2. Implement retry policy (max N, backoff strategy)
- 3. Add DLQ routing
- 4. Add monitoring hooks
- 5. Test failure and retry scenarios

## Forbidden shortcuts
- Never write non-idempotent job logic
- Never skip DLQ setup

## Questions to ask
- Which queue backend? (Redis/BullMQ, Celery, SQS)
- Max retry count and backoff multiplier?
- Who is alerted on DLQ events?

## Related domains
payment, webhook, notification

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
