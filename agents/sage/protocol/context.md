# Protocol context

Canonical vocabulary for Sage's request-shaping lifecycle. This file defines
terms only; rationale and implementation contracts live in decisions and flows.

## Route

**Definition:** The single shaping path Sage assigns before design based on
remaining decision fog and expected session span.
**Invariants:** Exactly one current Route owns the next shaping step; re-route
only when new facts change the amount or span of Fog.
**Includes:** `clear-single-session`, `foggy-single-session`,
`large-multi-session`.
**Excludes:** Risk level, task type, file count, checklist selection.
**Related:** Fog, Grill, Wayfinder, Flow.

## Fog

**Definition:** In-scope product/domain uncertainty that prevents design or
implementation without guessing.
**Invariants:** A repository fact that the agent can verify is never Fog and is
never delegated to the human as a product decision.
**Includes:** unresolved intent, terminology, scope, ownership, priorities, or
trade-offs; suspected questions not yet sharp enough to phrase.
**Excludes:** facts discoverable from code/schema/docs; work beyond Destination.
**Related:** Not yet specified, Out of scope, Frontier.

## Grill

**Definition:** A one-question-at-a-time HITL session that resolves
single-session Fog into confirmed requirements.
**Invariants:** The human owns HITL decisions; Grill records every answer before
moving to the next branch.
**Includes:** fact lookup, recommendations, scenario challenges, glossary
updates, checkpoint decisions.
**Excludes:** implementation design, product code, multi-session coordination.
**Related:** Requirements-clear, Flow, Wayfinder.

## Wayfinder

**Definition:** A durable multi-session planning map that coordinates decision
tickets until the route to a Destination is clear.
**Invariants:** The map indexes state while each ticket owns its resolution; a
session claims before work and closes at most one non-research ticket.
**Includes:** Destination, decision tickets, blocking, claims, Frontier,
Not yet specified, Out of scope.
**Excludes:** implementation tickets and delivery of the Destination.
**Related:** Map, Frontier, Grill, Flow.

## Destination

**Definition:** The explicit end state Wayfinder is finding a decision route to.
**Invariants:** It is bounded enough that map completion can be tested without
delivering the implementation itself.
**Includes:** a spec-ready handoff, an approved decision, or another named
planning outcome.
**Excludes:** unbounded future work or implementation tasks beyond that outcome.
**Related:** Out of scope, Map complete.

## Frontier

**Definition:** Open, unblocked, unclaimed Wayfinder tickets that a session may
work now.
**Invariants:** It is recomputed from ticket status, dependencies, and claims;
blocked or claimed tickets never appear in it.
**Includes:** tickets whose `blocked_by` dependencies are closed.
**Excludes:** blocked, claimed, closed, or out-of-scope tickets; unphraseable Fog.
**Related:** Ticket, Not yet specified.

## Requirements-clear

**Definition:** Grill's exit state: product intent, canonical terms, scope, and
trade-offs are resolved with no implementation-shaping HITL decision left open.
**Invariants:** Flow may reopen a settled product decision only when it cites
new contradictory code or schema evidence.
**Includes:** a confirmed chat handoff or checkpoint spec.
**Excludes:** completed implementation design.
**Related:** Grill, Flow, Design-clear.

## Flow

**Definition:** Implementation design performed from clear requirements against
real code/schema.
**Invariants:** Flow owns implementation decisions and does not repeat Grill's
product interview.
**Includes:** systems, APIs, state, failures, security, concurrency, rollout.
**Excludes:** re-interviewing resolved product decisions or coordinating
multi-session Fog.
**Related:** Requirements-clear, Design-clear.
