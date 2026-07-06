# /sage-flow — turn a feature/journey into an implementation-ready business flow

Take a described flow (a feature, a user journey, a business process) and produce
a complete, end-to-end **business flow document** that any engineer — on any
stack, in any language, across one or many repos — can implement from without
guessing. The output names every system involved, every API (existing + new),
every piece of state, every error path, and who builds what.

**This skill is stack-agnostic.** It works for a TypeScript web app, a Go
service, a Python worker, a mobile app, an embedded system, or a mix. Never
assume a framework — detect it from the code, or describe the flow in
system-neutral terms (systems, endpoints, storage, messages) when the target is
unknown.

> **Invoked by the run checklist.** When `plan-flow` is active (§0 of `AGENTS.md`),
> Sage runs this command itself before writing code — the human does not call it
> manually. `/sage-flow` is the **build** half of `plan-flow`; the **verify** half
> lives in Step 4 below.
>
> **Shape & prose** follow the shared style-guide
> [`agents/sage/docs-style-template.md`](agents/sage/docs-style-template.md)
> (ASCII overview rules, "when → then", concrete-over-abstract). `/sage-flow` is
> the **pre-code design** artifact (reuse-vs-build, cross-repo contracts) written
> to `agents/sage/flows/`; `/sage-docs` is the **post-code** human doc in `docs/`.

---

## Model & effort — read the session ceiling first

Follow the same discipline as `/sage`: detect the current session **model +
effort** and never exceed either. **Flow design is never downgraded** — the whole
command (build **and** verify) runs at the **full session model + effort**, never
a lower tier. It is the highest-reasoning step there is; `auto-switch-model` may
lower other trivial sub-tasks, never this one. The only cap is the session
ceiling itself — never raise above it. State the ceiling once in the intent block.

---

## Step 1 — Load role (`architect`, handing off as needed)

Open `agents/sage/roles/role-architect.md`:

- **Found** → read and adopt. Output: `Role: architect [loaded]`
- **Missing** → create it (persona: draws clean system boundaries, decides what
  belongs in which service/store/token, makes failure and idempotency explicit),
  output: `Role: architect [created]`

A flow may span domains (frontend, backend, payments, data). Load the relevant
domain role when you reach that system's section and output the handoff line.

> **Multi-repo:** if the flow crosses repos, anchor every path (`agents/sage/`,
> role files) to the repo that owns the file you're writing. State each repo root
> once in the intent block. Never write one repo's knowledge into another.

---

## Step 2 — Ground the flow in reality (do NOT invent)

Before writing a single step, discover what already exists. Source is
authoritative — never infer an API, table, or contract from a name.

1. **Identify the systems/actors.** Website/app, each backend service, each
   external provider, queues, cron, the user roles. Draw the trust boundary:
   who owns money/ids/secrets, who is allowed to compute what.
2. **Find existing assets per system.** Endpoints, data models/tables, shared
   utils, auth/session handling, existing pages/screens, existing state stores.
   Open the real files and read the exports/signatures/fields. Fan out with
   parallel search agents when the surface is large.
3. **Separate reuse vs build.** For every capability the flow needs, decide:
   already exists (reuse), exists but must change, or missing (build new).
4. **Surface the conflicts early.** Ambiguity, missing business rules, a step
   that contradicts another (e.g. "don't call the API yet" vs "show the price").
   Ask one focused question only when the answer changes the design.

If a domain folder under `agents/sage/` exists for a system, read its `rules.md`
and relevant `decisions/` and quote what applies.

---

## Step 3 — State intent + get approval

Output this block, then wait for `ask`/`reject` before writing the full doc:

```text
Repos   : <repo → responsibility>  (list each when >1)
Role    : architect — <flow name in one line>
Model   : <model> @ effort:<effort>  ← session ceiling
Systems : <website / service-A / payment-service / gateway / …>
Reuse   : <what already exists>
Build   : <what's missing / must change>
Unknowns: <open questions that block design>
Risk    : LOW | MEDIUM | HIGH — <why>
Decision: proceed | ask | reject
```

---

## Step 4 — Write the flow document

Write to `agents/sage/flows/<slug>-flow.md` (in the repo that owns the flow's
entry point; for a pure backend flow, the backend repo). Derive `<slug>` from the
flow name. If the doc exists, update in place.

**Language:** match the language the user is working in (the conversation / the
existing docs). Keep technical tokens (method, path, table, field, status, key,
type/DTO names) in their real form — they never get translated.

The document MUST contain these sections, in order. Adapt names to the flow, but
never drop one without saying why it's N/A.

1. **Header + design decisions** — one-paragraph summary, date, links to related
   `decisions/`. Call out any non-obvious design choice up front (e.g. "record is
   created only at payment, not at review").
2. **Actors & Systems** — table of every system + its responsibility +
   ownership. Then the **trust boundary**: who owns ids/money/secrets, who may
   compute/store what, what each system must NOT do.
3. **End-to-end overview** — one linear diagram (ASCII per the style-guide)
   tracing the whole journey across systems, including the server-to-server paths
   (webhooks, callbacks) and the client paths (redirects), marking which is the
   source of truth.
4. **Step-by-step** — each step says **which system acts**, what it does, which
   API it calls (name + method + path), and the exact when → then → outcome. One
   branch per line. Cover the happy path and every alternate path.
5. **State / data handling** — every piece of state: where it lives (client
   store, DB row, cache, token), its shape, its lifecycle (created when, updated
   when, cleared when, TTL). Call out what must NOT be trusted client-side.
6. **API spec — all systems** — for EACH system, a table/spec of endpoints split
   into **reuse (exists)** and **build new**. For every new endpoint give
   method, path, request shape, response shape (with real error codes), and side
   effects. Include the internal/service-to-service and provider endpoints, not
   just the public ones.
7. **Cross-repo work** (include only when >1 repo) — for each repo: what it
   builds, the integration contract with the others (request/response/event
   shape), the sequence of who-calls-who, deployment/versioning order, and where
   each repo's knowledge is captured. Make the contract explicit enough that the
   two teams can build in parallel against it.
8. **Status lifecycle** — every status value, its meaning, who sets it, the legal
   transitions. Note any schema default that this flow overrides.
9. **Data model touchpoints** — the tables/entities touched and their key fields
   (reuse existing; flag new columns/migrations).
10. **Edge cases & error handling** — a table of concrete failure scenarios →
    handling (refresh mid-flow, double-submit, provider down mid-transaction,
    duplicate webhook, timeout, expired, permission mismatch, empty selection).
11. **Security & concurrency** — authz/ownership (IDOR), where money/ids are
    computed, secret ownership, **idempotency** points, atomicity/rollback,
    amount/signature verification, race conditions.
12. **Build checklist** — grouped per system/repo, each item a concrete unit of
    work, checkbox form.
13. **Open questions** — the decisions still needed before/while building; mark
    any that are already resolved.

**Quality bar (govern every section):**

- **Concrete over abstract** — `409 { conflictItems: [...] }` beats "return an
  error"; `UPDATE trn_submit SET payment_status='C'` beats "save the status".
  Use real names.
- **When → then → outcome** — every branch traceable top-to-bottom; every path
  ends in a clear outcome.
- **Source of truth is explicit** — for any dual-path result (webhook vs
  redirect, cache vs db), say which one decides and why.
- **Idempotency & atomicity are called out** wherever money or external calls
  happen — never leave "what if this is retried / half-fails" unanswered.
- **The test:** someone who has never seen the code can implement every branch,
  in the right system, from the doc alone.

**Verify the flow ("should it really be this way?") — the second half of
`plan-flow`.** Before you finish, review the doc as a skeptic, not its author:
re-check each step against the real code/schema, hunt the weak points (wrong
trust boundary, a missed error path, a step that contradicts a rule, a simpler
route), make sure every uncertainty is in §13 Open Questions, and **ask the human
the risky/ambiguous ones now** — do not code past a doubt.

---

## Step 5 — Capture knowledge (mandatory)

The flow doc lives in `agents/sage/flows/`. Additionally capture the reusable
**pattern** (not the specifics) as a decision so the next flow benefits:

- **A — New pattern** → `agents/sage/<domain>/decisions/<slug>.md`. Write the
  pattern + why + Do/Avoid. `enforcement: advise`, `source: ai`,
  `status: proposed`. Example: "Create the transactional record only at the
  pay/commit step, never at the review step — no server-side draft garbage from
  abandoned journeys."
- **B — Updated** an existing decision → note accurate/stale, update in place.
- **C — None** → state `No new knowledge — <file> covers this`.

For multi-repo flows, write each repo's pattern into that repo's `agents/sage/`.

---

## Step 6 — Summary (mandatory — a response without this is incomplete)

Output as plain markdown (no code fence):

```markdown
── Sage Flow ─────────────────────────────────────
**Role** · architect — <flow in one line>
**Model** · <model> @ effort:<effort>
**Systems** · <list> | **Repos** · <list> | **Risk** · <LOW|MEDIUM|HIGH>

**Flow doc** · `agents/sage/flows/<slug>-flow.md`

**Shape**
Summarise the journey in 2–3 sentences: entry → key steps → exit, naming the
system that owns each critical decision.

**Reuse vs build**

- Reuse: <existing endpoints/models/components>
- Build: <new endpoints/services/pages, grouped by system/repo>

**Cross-repo** (omit if single repo)

- <repo> builds <X>; contract with <repo> is <shape>; build order <…>

**Open questions**

- <the decisions still blocking implementation>

**Knowledge** · [new | updated | none] `<path>` — <pattern title>
──────────────────────────────────────────────────
```

Then stop. The human confirms the open questions before implementation begins.
