# notification rules

Multi-channel notification system

## Business rules
- Notifications must be async — never block main flow
- User notification preferences must be respected
- Failed notifications must be retried, not silently dropped
- Notification content must not contain sensitive data in plain text

## Common requirements
- Multi-channel support (email, SMS, push, in-app)
- Template system for notification content
- User preference management (opt-out per channel/type)
- Retry logic for failed deliveries
- Delivery tracking and audit log

## Risk flags
- Notification provider downtime can cascade if not async
- Sending duplicate notifications on retry without idempotency

## Required workflow
- 1. Trigger notification event → enqueue
- 2. Worker: load user preferences → select channel → render template
- 3. Send via provider → log delivery status
- 4. Retry on failure

## Forbidden shortcuts
- Never send notifications synchronously in request flow
- Never hardcode notification content — use templates

## Questions to ask
- Which providers? (SendGrid, Twilio, FCM, etc.)
- Does user have per-channel opt-out preference?
- Is notification history visible to user?

## Related domains
worker, user, audit

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
