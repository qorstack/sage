---
id: keep-context-separate-from-decisions
type: team_decision
title: Keep context separate from decisions
domain: protocol
tags: [context, glossary, decisions, checkpoint]
status: proposed
enforcement: warn
applies_to: [protocol, "agents/sage/**/context.md", "agents/sage/flows/**"]
source: ai
supersedes: ""
related: [route-by-fog-and-session-span]
timestamp: 2026-07-17T00:00:00Z
---

Use a domain `context.md` only for canonical vocabulary: definition, semantic
invariants, examples/includes, non-examples/excludes, and related terms. Update
it as soon as Grill settles an overloaded term so later questions use the same
meaning.

Keep request-specific answers and open questions in the durable spec checkpoint,
and keep hard-to-reverse team choices in one-decision-per-file decision entries.
Do not turn the glossary into a second plan, ADR store, or session transcript.
