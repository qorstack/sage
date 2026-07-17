---
id: risk-drivers-own-controls
type: team_decision
title: Risk drivers own controls
domain: protocol
tags: [risk, controls, validation, evidence]
status: proposed
enforcement: block
applies_to: [protocol, "AGENTS.md", "agents/sage/commands/**"]
source: ai
supersedes: ""
related: []
timestamp: 2026-07-17T00:00:00Z
---

Risk level chooses the gate; the concrete risk driver chooses the required
control. Never treat `LOW | MEDIUM | HIGH` as a header-only label, map every HIGH
risk to the same specialist, or let an unchecked specialist remove a core
control.

Before implementation, name the affected asset, failure mode, confidence, and
driver-specific evidence required. After validation, lower residual risk only
when actual evidence reduces likelihood/exposure or improves reversibility.

This keeps controls relevant: a HIGH migration needs backup/dry-run/rollback,
while a HIGH authorization change needs ownership and negative-permission proof.
