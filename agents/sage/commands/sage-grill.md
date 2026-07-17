# /sage-grill — resolve single-session fog and preserve the decisions

Turn a `foggy-single-session` request into `requirements-clear`: product intent,
canonical terminology, scope, and trade-offs the human has actually confirmed.
Ask one decision at a time, ground facts in the repo, maintain the domain glossary
inline, and checkpoint multi-decision sessions so alignment survives the chat.

**Produces decisions, not product code.** It stops before design or
implementation. It is an always-on routing guard independent of `plan-flow`, not
a sixth checklist item. If the effort is larger than one session, hand it to
`/sage-wayfinder` instead of forcing this command to hold the whole map.

---

## Model & effort

Run at the full session model + effort ceiling. Grilling decides the shape of
everything downstream; never downgrade it or exceed the session ceiling. If the
environment hides model/effort, state `current agent @ effort:unavailable`.

---

## Step 1 — Load the lens and domain model

Load the request's senior lens per `AGENTS.md` §1.1. Read, in order:

1. `agents/sage/<domain>/index.md`
2. `agents/sage/<domain>/context.md` when present
3. `rules.md` and relevant `decisions/*.md`
4. real source, schema, config, docs, and git facts for the request

A question answerable from the environment is research skipped, not a human
decision. When the human's description conflicts with code/schema, surface both:
`code currently does X; the requested domain behavior says Y` — then ask which
behavior should become authoritative. Never silently bend one to match the other.

`context.md` is a glossary only. Challenge fuzzy/conflicting language against it
and use the exact format in `AGENTS.md` §2. Do not put implementation details,
decision rationale, or temporary notes there.

---

## Step 2 — Build the decision tree and confirm the route

Separate:

- **Facts** — discoverable from code/schema/docs/git/tools. Look them up.
- **Decisions** — product intent, scope, priorities, canonical terms, risk
  appetite, and trade-offs between valid outcomes. Only these become questions.

List sharp decisions in dependency order. Fog that cannot yet be phrased stays
`not-yet-specified`; never invent a fake ticket/question. If the tree, research,
or prototypes cannot reasonably fit this session, output
`Route: large-multi-session` and hand the request to `/sage-wayfinder`.

Otherwise output `Route: foggy-single-session` and continue.

---

## Step 3 — Start the durable checkpoint before questioning

Create `agents/sage/flows/<slug>-spec.md` **before the first question** when any
condition is true:

- more than one sharp decision is open;
- the conversation may cross a session/context boundary;
- multiple systems/repos or people depend on the answers;
- the human asks for a durable artifact.

Use this shape:

```markdown
# <Request> — decision spec

Status: grilling
Last updated: <ISO-8601>
Route: foggy-single-session

## Problem
## Success outcome
## Decisions
## Out of scope
## Still open
## Not yet specified
## Terms changed
## Evidence / source pointers
```

After **every** human answer, update `Decisions`, `Still open`, `Out of scope`,
`Terms changed`, and `Last updated` before asking the next question. Store full
rationale once in the spec; summaries link to it instead of copying it. A single
small decision may remain chat-only, but write a spec at the end if it should
outlive the conversation.

---

## Step 4 — Grill one decision and stress-test it

For each decision:

1. Ask the single most-blocking question precisely.
2. Recommend one answer and give one concise reason.
3. Wait. A HITL decision is never answered by the agent.
4. Sharpen overloaded terms before building on them.
5. For a **material decision** — one that changes user behavior, domain
   relationships, data/trust ownership, scope, or a hard-to-reverse trade-off —
   test the proposed answer with at least one concrete boundary/counterexample:
   retry, partial failure, permission mismatch, empty/expired state, conflicting
   term, or another scenario specific to the domain.
6. If the scenario breaks the answer, reopen/refine it; do not mark it decided.
7. Record the answer/checkpoint before continuing.

When a canonical term is resolved, update
`agents/sage/<domain>/context.md` **immediately** and add/list it in the domain
index. Do not batch glossary writes until the end.

---

## Step 5 — Exit with a contract, not more questions

Exit only as `requirements-clear`, after the human confirms shared understanding.
The handoff must contain:

- product intent and success outcome;
- canonical terms used by the request;
- scope and explicit out-of-scope;
- resolved product/domain trade-offs;
- no open HITL decision that changes implementation shape.

`/sage-flow` owns newly discovered implementation decisions: system boundaries,
APIs, state, failure paths, security, concurrency, and rollout. It must not ask a
resolved product question again unless new code/schema evidence contradicts it;
then it reopens the named decision and cites the evidence.

If fog grows beyond this session at any point, checkpoint current state and hand
off to `/sage-wayfinder`; `/sage-flow` accepts only a clear, implementation-ready
handoff.

---

## Step 6 — Capture glossary and durable decisions correctly

- Canonical vocabulary → `agents/sage/<domain>/context.md` immediately.
- Request-specific agreement → checkpoint spec.
- Reusable rule/pattern → knowledge capture per `AGENTS.md` §3.
- ADR-like `decisions/<slug>.md` from grilling → write only when **all three** are
  true: hard to reverse, surprising without context, and chosen through a real
  trade-off. Otherwise the spec/glossary is enough.

Update the domain index whenever `context.md` or a decision is added.

---

## Step 7 — Summary

```markdown
── Sage Grill ────────────────────────────────────
**Role** · <lens> — <request>
**Model** · <model> @ effort:<effort>
**Route** · foggy-single-session → requirements-clear
**Domain** · <domain> | **Initial risk** · <LOW|MEDIUM|HIGH> · confidence:<level>

**Decided**

- <decision → answer; scenario used to validate material decisions>

**Terms updated**

- <term → `agents/sage/<domain>/context.md`, or "none">

**Out of scope**

- <explicit boundary>

**Still open** · None — requirements-clear
**Checkpoint** · <spec path | not written — single small decision>
**Required controls handed off** · <driver → control/evidence>
**Knowledge** · [new | updated | none] `<path>` — <reason>
──────────────────────────────────────────────────
```

Stop. The next command consumes this handoff; it does not restart the interview.

---

_The one-question-at-a-time fact/decision discipline is adapted from Matt
Pocock's `grilling`; inline glossary and scenario stress-testing are adapted from
`domain-modeling` (MIT). Sage adds routing, checkpoints, risk controls, and the
explicit Grill → Flow exit contract._
