# otp rules

One-time password flows (SMS/email verification)

## Business rules
- OTP must expire (5–10 minutes is standard)
- OTP must be single-use — invalidate on first use
- Max OTP retry limit before lock (3–5 attempts)
- Resend must have cool-down (60 seconds minimum)
- OTP must not be logged in plain text

## Common requirements
- Generate cryptographically random OTP (6 digits / UUID token)
- Store hashed OTP with expiry timestamp
- Resend flow with cool-down enforcement
- Lock account/IP after max retries
- Notification provider integration (SMS or email)
- Audit log OTP requests and verification attempts

## Risk flags
- OTP sent over SMS can be intercepted (SIM swap) — consider authenticator app for sensitive ops
- Not expiring OTPs is a critical security flaw
- Predictable OTPs (sequential, timestamp-based) are exploitable

## Required workflow
- 1. Generate OTP → hash → store with expiry
- 2. Send OTP via notification provider
- 3. Verify: check hash + expiry + retry count
- 4. Invalidate on success; increment counter on failure
- 5. Lock after max retries

## Forbidden shortcuts
- Never store OTP in plain text
- Never skip expiry check
- Never allow unlimited retries

## Questions to ask
- Notification channel: SMS, email, or authenticator app?
- OTP length and expiry window?
- Max retry count before lock?
- Should lock be per-user or per-IP?

## Related domains
auth, notification, audit

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
