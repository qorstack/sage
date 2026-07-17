---
id: route-by-fog-and-session-span
type: team_decision
title: Route by fog and session span
domain: protocol
tags: [routing, grill, wayfinder, flow]
status: proposed
enforcement: block
applies_to: [protocol, "AGENTS.md", "agents/sage/commands/**"]
source: ai
supersedes: ""
related: [keep-context-separate-from-decisions]
timestamp: 2026-07-17T00:00:00Z
---

Route a code request by unresolved decision fog and expected session span, not
by file count alone. A clear request goes directly to Flow when `plan-flow` is
enabled, a foggy request that fits one session goes through Grill, and work with
unresolved decisions spanning multiple sessions goes through Wayfinder.

This routing guard is independent of the optional `plan-flow` toggle. Grill
must produce a requirements-clear handoff, Wayfinder must produce a durable
spec-ready handoff, and Flow must not re-interview settled product decisions
without new contradictory evidence from code or schema.
