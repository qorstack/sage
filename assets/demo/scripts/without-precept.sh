#!/usr/bin/env bash
# Mock "Claude with no Precept" session — used by ../without-precept.tape
# to produce a deterministic GIF. Pure printf + sleep, no real AI involved.

set -e
slow() { printf "%s\n" "$1"; sleep "${2:-0.6}"; }

printf '\033[1;36m$\033[0m claude "add Google SSO to /login"\n'
sleep 0.9
printf "\n"
slow "⚙  Reading repo..." 1.0
slow "✓  Created auth/sso/google.ts" 0.5
slow "✓  Created OAuthClient.ts" 0.5
slow "✓  Stored access_token in localStorage" 0.5
slow "✓  Committed: feat(auth): Google SSO" 1.5
printf "\n"
slow "── 2 days later, in PR review ──" 0.9
slow "reviewer: We already have AuthService —" 0.5
slow "          why a new OAuthClient?" 0.9
slow "reviewer: Tokens in localStorage??" 0.5
slow "          that breaks our session policy." 1.6
printf "\n"
printf "\033[1;31m→ Revert. Rewrite. Re-review.\033[0m\n"
sleep 2.5
