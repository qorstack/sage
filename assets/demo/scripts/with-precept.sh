#!/usr/bin/env bash
# Mock "/precept" session — used by ../with-precept.tape to produce a
# deterministic GIF. Mirrors the real `precept analyze` output but scripted
# so the recording is reproducible (real CLI output depends on repo state).

set -e
slow() { printf "%s\n" "$1"; sleep "${2:-0.4}"; }

printf '\033[1;36m$\033[0m claude /precept "add Google SSO to /login"\n'
sleep 0.9
printf "\n"
slow "⚙  analyze_intent..." 1.3
printf "\n"
slow "┌──────────────────────────────────┐" 0.05
slow "│ Domain:   \033[1;31mauth (HIGH)\033[0m            │" 0.5
slow "│ Decision: \033[1;33mASK\033[0m                    │" 0.5
slow "│ Reuse:    AuthService,           │" 0.3
slow "│           SessionStore           │" 0.5
slow "│ Rule:     \"Sessions live         │" 0.3
slow "│            server-side — never   │" 0.3
slow "│            localStorage\"         │" 0.3
slow "│           (alice, approved)      │" 0.6
slow "│ Risk:     auth → session →       │" 0.3
slow "│           audit log              │" 0.5
slow "└──────────────────────────────────┘" 0.05
printf "\n"
sleep 1.0
printf "\033[1;33m⏸\033[0m  Pausing for human sign-off.\n"
sleep 3.0
