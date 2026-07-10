# /sage-grill — interrogate a foggy request into agreed decisions

Take a request that is **not yet clear enough to build** — an ambiguous feature,
a vague "make it better", a design with unstated trade-offs — and turn it into a
small set of **decisions the human has actually agreed to**, by grilling one
question at a time. This is the step that stops Sage from confidently building the
wrong thing: most failures are not bad code, they are unspecified requirements.

**This skill produces decisions, not deliverables.** It writes no product code.
It ends when the way is clear — when nothing is left to decide before `/sage-flow`
or implementation can start.

> **Invoked before design.** Sage runs `/sage-grill` **before `/sage-flow`** when
> the request is foggy (an ambiguous ask, two defensible designs, a risky
> assumption, an overloaded term). It is on-demand, not a locked checklist item —
> the five-choice picker in `AGENTS.md` §0 stays exactly five. When the request is
> already sharp, skip straight to the flow and say so.
>
> **Shape & prose** follow the shared style-guide
> [`agents/sage/docs-style-template.md`](agents/sage/docs-style-template.md).

---

## Model & effort — read the session ceiling first

Grilling is a **deep** reasoning step — it decides the shape of everything built
after it. Run it at the **full session model + effort** (the ceiling); never
downgrade it, never exceed the ceiling. If the environment does not expose the
model/effort, write `Model : current agent @ effort:unavailable` and continue.

---

## Step 1 — Load role + ground yourself in reality

Load the senior lens the request implies (`architect` for design questions, the
domain role otherwise) per `AGENTS.md` §1.1 — output the `Role:` line. Then read
the relevant `agents/sage/<domain>/rules.md` and `decisions/` so you grill from
what the team already decided, not from a blank slate.

**Before you ask the human anything, look first.** Open the real source, schema,
and config for the area in question. A question you can answer from the code is
not a question — it is research you skipped.

---

## Step 2 — Separate facts from decisions

This is the rule that makes grilling sharp:

- **Facts** — anything discoverable in the code, schema, docs, or git: does this
  export exist, what does this table allow, how does the current flow behave.
  **Look these up yourself. Never ask the human a fact.**
- **Decisions** — the calls that are genuinely the human's: product intent,
  trade-offs between two valid designs, scope, priorities, risk appetite. **These,
  and only these, become questions.**

List the open decisions as a **decision tree** — which ones depend on which. You
will walk it top-down, resolving prerequisites first.

**Only list a decision when its question is already sharp enough to phrase
precisely.** Fog you cannot yet phrase stays as a single `not-yet-specified`
note — resolving the sharp questions usually sharpens it into a real question
later. Never invent a decision you cannot yet state.

---

## Step 3 — Grill: one question at a time

Walk the decision tree and put each decision to the human **one at a time** — a
wall of questions is confusing and gets skimmed.

For **each** question:

1. Ask the single most-blocking open decision, phrased precisely.
2. **Propose your recommended answer** and one line of why — you are a senior
   giving a steer, not a blank survey.
3. **Sharpen fuzzy terms on the spot.** If a word is overloaded ("account →
   Customer or User?", "sync → real-time or eventual?"), pin the meaning before
   building on it.
4. **Wait for the reply.** Do not ask the next question, and do not start
   designing, until this one is answered.

Record each answer as it lands. When a decision changes the scope, update the
`Out of scope` list — say explicitly what this request will **not** do.

**A HITL decision is never answered by the agent.** If a decision is truly the
human's, you may recommend, but you do not decide it for them and move on.

---

## Step 4 — Stop when the way is clear

Grilling is done when every sharp decision is resolved and the human has
confirmed a **shared understanding** — not before. If new fog surfaced that is
too big to resolve here, hand it to `/sage-flow`'s decision-map mode (a large
effort charted as decisions) rather than forcing an answer.

Do not enact anything. The next step (`/sage-flow` or implementation) begins only
after the human confirms.

---

## Step 5 — (Optional) write the agreed decisions to a spec

For a feature big enough that the decisions should outlive the chat, write them
to `agents/sage/flows/<slug>-spec.md` so `/sage-flow` and implementation inherit
them. Synthesize only what was agreed — do **not** re-interview. Sections:

1. **Problem** — the challenge in the human's words.
2. **Solution** — the agreed user-facing approach.
3. **Decisions** — each resolved decision + the reason it went that way.
4. **Out of scope** — what was explicitly ruled out (never silently graduates
   back in).
5. **Open / deferred** — decisions pushed to the flow step, if any.

---

## Step 6 — Capture knowledge (mandatory)

Grilling often surfaces a durable team decision (a product rule, a naming
convention, a trade-off the team keeps making). Capture the **pattern** per
`AGENTS.md` §3 — but clear the noise bar: only what is hard to reverse,
non-obvious, or a genuine trade-off. Otherwise state `No new knowledge`.

---

## Step 7 — Summary (mandatory — a response without this is incomplete)

Output as plain markdown (no code fence):

```markdown
── Sage Grill ────────────────────────────────────
**Role** · <lens> — <request in one line>
**Model** · <model> @ effort:<effort>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Decided**

- <decision> → <agreed answer> (recommended: <yes/changed by human>)

**Out of scope**

- <what this will deliberately not do>

**Still open**

- <decisions deferred to /sage-flow, or "None — ready to build">

**Spec** · <`agents/sage/flows/<slug>-spec.md`, or "not written — small change">

**Knowledge** · [new | updated | none] `<path>` — <pattern or reason>
──────────────────────────────────────────────────
```

Then stop. The human confirms before `/sage-flow` or implementation begins.

---

_The one-question-at-a-time grilling technique — facts you look up yourself vs.
decisions you put to the human, each with a recommended answer — is adapted from
[Matt Pocock's skills](https://github.com/mattpocock/skills) (`grilling`, MIT).
Sage folds it into its own pipeline (role → knowledge → grill → flow → capture)
rather than shipping it as a standalone command._
