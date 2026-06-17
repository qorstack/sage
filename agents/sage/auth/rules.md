# auth rules

Authentication and authorization domain

## Business rules
- Passwords must never be stored in plain text
- JWT tokens must have expiration
- Failed login attempts must be rate-limited (max 5/15min is a safe default)
- Session invalidation must be possible (logout from all devices)
- Sensitive auth events must be audit logged

## Common requirements
- Register / Login / Logout flows
- Token refresh mechanism
- Password reset via email/OTP
- Rate limiting on auth endpoints
- Brute force protection
- Audit logging for login/logout/failed attempts
- Notification for suspicious login (new device/location)

## Risk flags
- Changing token signing key invalidates all active sessions
- Changing session strategy may log out all users
- Removing auth middleware can expose protected routes

## Required workflow
- 1. Define auth flow (register → verify → login → refresh → logout)
- 2. Choose token strategy (JWT / session / OAuth)
- 3. Implement rate limiting before exposing endpoints
- 4. Add audit logging
- 5. Test brute force scenarios
- 6. Security review before production

## Forbidden shortcuts
- Never disable rate limiting 'temporarily'
- Never log raw passwords or tokens
- Never use MD5/SHA1 for password hashing — use bcrypt/argon2

## Questions to ask
- Which token strategy: JWT, session, or OAuth provider?
- What is the token expiry window?
- Which notification provider for login alerts?
- Is 2FA/MFA required?

## Related domains
user, audit, notification

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
