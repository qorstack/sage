---
name: docs-style-template
type: convention
status: approved
domain: docs
applies_to: "docs/**/*.md"
source: human
---

# Sage Docs — Markdown flow style-guide (canonical)

The one reference for what a `/sage-docs` output should look like. Docs are
**plain Markdown** (`docs/<slug>.md`) — no HTML, no CSS, no JS, no browser. A doc
is read on GitHub, in an editor, in a PR diff. It must be **complete, concrete,
and read top-to-bottom** like a senior engineer explaining the flow end-to-end.

> The gold-standard example this guide is modeled on is a real flow doc that
> reads top-to-bottom with an ASCII overview, full step-by-step, and complete API
> spec (e.g. `docs/<feature>-business-flow.md`). When in doubt, match its depth —
> it is never abbreviated.

---

## Non-negotiables

1. **Markdown only.** `.md`, not `.html`. Diagrams are **ASCII/text inside a
   fenced code block**, not SVG or Mermaid — they render everywhere and diff
   cleanly.
2. **One language, never mixed.** All prose in the chosen language (English by
   default; ask every time). Technical tokens (method, path, table, field,
   status, key, DTO) keep their real names and do not count as mixing.
3. **Complete, not summarized.** The doc is the artifact. Never cut a guard, an
   error path, or a side effect to keep it short. Brevity means cutting empty
   connectors, never conditions.
4. **Concrete over abstract.** `422 { error: 'cart_empty' }` beats "return an
   error". `UPDATE orders SET status='paid'` beats "save the status". Use real
   names throughout.
5. **Multi-repo aware.** When a flow spans systems in different repos, every
   step/endpoint names **which system owns it** (see the Actors table).

---

## Principles of good docs (govern every section)

Easy to read **+** complete conditions **+** concise — all three at once:

1. **Answer-first** — open each section with one sentence on what it does, before
   the details.
2. **One idea per line** — each condition / branch / error on its own line.
3. **Concise = cut connectors, not conditions** — drop "in the case that", "which
   will then"; keep every guard, error, and side effect.
4. **Show branches as when → then** — "when X → do Y → return Z", traceable
   top-to-bottom.
5. **Cover every exit** — one happy path + every error path. If a response table
   lists 422 and 409, the logic must show both.

> **The test:** someone who has never seen the code can re-implement every branch
> from the doc = complete · you can delete words without losing meaning = not yet
> concise enough.

---

## Document skeleton (top-to-bottom)

The section set flexes with the doc type (see below), but a full flow doc reads
in this order:

```text
# Title — <feature> (<system scope in parens>)
> 2–4 line blockquote: what this flow is, which systems it spans, "refs real code as of <date>"

## 1. Actors & Systems         table: system | responsibility | ownership  (+ trust boundary)
## 2. End-to-end overview       ONE ASCII flow of the whole thing + a "Key/หัวใจ" callout
## 3. Step-by-step              STEP 1..N — each names its system(s), APIs, actions, business rules
## 4. State / data lifecycle    (if the flow holds client/session state)
## 5. API spec                  every endpoint, grouped by system: request + response JSON, guards, side effects
## 6. Status lifecycle          state codes + who sets each + allowed transitions (if any)
## 7. Data model                tables/entities touched + their role in the flow
## 8. Edge cases & errors       table: case → handling  (every failure mode)
## 9. Security & concurrency    authz, idempotency, trust boundaries, amount/lock checks
## 10. Build checklist          per-system `- [ ]` list of what to create/change
## 11. Open questions           numbered — what must be confirmed before implementing
```

Drop sections that don't apply (a `runbook` has no API spec; a `data-schema` is
mostly §7). Never drop §11 when anything is uncertain — that is where
`plan-flow`'s **verify** step lands.

---

## The overview ASCII flow (§2) — the centerpiece

One fenced code block showing the whole flow in order. Rules:

- **Vertical spine** with `│ ▼` for the main path; label each arrow with the
  action **and** the call that carries it.
- **Name the system** at each hop: `[Website] …`, `[Service] …`,
  `[Gateway] …` — so a reader sees the boundary being crossed.
- **Show the real call on the arrow:** `POST /api/TrnSubmits/{id}/pay`, not "pay".
- **Branches** use `├─(A)` / `└─(B)` with a one-line note on each.
- **Nested calls** indent under their caller with `└─`.
- Follow the block with a **key insight** line (`**Key:** …` / `**หัวใจ:** …`)
  stating the one thing a reader must not miss (e.g. "trust the webhook, not the
  redirect").

Skeleton:

```text
[User] <action that starts the flow>
   │
   ▼ <gesture> ── <System>: <what happens> (<call or "no API">)
   │
[System A] <page/handler>
   │  ── <System B>: POST /api/... (<purpose>)
   │  ── <System B>: GET  /api/... (<purpose>)
   │
   ▼ <decision / user action>
   │  ── <System A> → <System B>: POST /api/.../action
   │        └─ <System B> → <System C>: <nested call>
   │              └─ <System C> → <System B>: returns { ... }
   │
   ├─(A) <trusted path — server-to-server>  → <outcome>
   └─(B) <untrusted path — client redirect>  → <outcome>
   │
[System A] <final page> → <terminal state>
```

Keep it tight: consistent indentation, no stray characters, the whole flow on
one spine. This block and the §3 steps must tell **the same story** — every hop
in the diagram has a STEP below it.

---

## Step-by-step (§3)

One `### STEP n — <title>` per hop. Each step states:

- **System:** which system(s) this step runs in (bold line right under the
  heading).
- **APIs used** — full `METHOD /path` with a one-line purpose; mark whether it
  **already exists** or **must be built**.
- **Actions** — the concrete work, one idea per line (state writes, navigation,
  guards). Use real key/field names.
- **Business rules** — the exact numbers/formulas (`VAT 7% → 350`, flat rate,
  ranges), not "calculate the fee".

Mirror the overview: if STEP 3 fans out to A and B, the step text explains both.

---

## API spec (§5)

Group by system (`### 5.1 <System> — existing (reuse)`, `### 5.2 <System> — new`).
For **each endpoint**:

- heading: `#### METHOD /path — <purpose>`
- a fenced `jsonc` block with **`// Request`** and **`// Response 200`** (+ every
  non-2xx it can return, e.g. `// Response 409 — <when>`), using real field
  names and example values.
- **Guard:** the authz / state precondition (IDOR check, `status == 'N'` only, …).
- **Side effect:** every write / external call / event this endpoint causes.
- **Idempotency:** state it explicitly for anything that moves money or fires on
  a retryable webhook.

---

## Tables to prefer

- **Actors:** `| System | Responsibility | Ownership |`
- **Status lifecycle:** `| Code | Meaning | Set by |` + a `Transition:` line.
- **Data model:** `| Table | Role in this flow |`
- **Edge cases:** `| Case | Handling |` — one row per failure mode.
- **Build checklist:** grouped `- [ ]` lists per system.

Keep tables narrow (2–3 columns). Long detail goes in prose or a `jsonc` block,
not a wide table.

---

## Doc types (pick one, shapes the section set)

| Type            | Pick when                                                  | Leans on                           |
| --------------- | ---------------------------------------------------------- | ---------------------------------- |
| `api-flow`      | frontend/client calling backend endpoints                  | §2 spine, §3 steps, §5 API spec    |
| `backend-logic` | server-side processing — conditions, storage, side effects | §3 branches, §5, §8 edge cases     |
| `frontend`      | component tree, state flow, API calls from the UI          | §3 per-component, §4 state         |
| `architecture`  | system components and their relationships                  | §1 actors, §2 graph, §7 model      |
| `user-journey`  | steps a user takes through a feature                       | §2 spine, §3 steps                 |
| `runbook`       | operational procedure — setup, deploy, debug               | §3 steps, §8 failures (no §5)      |
| `data-schema`   | data models, entity relationships                          | §7 model (per-entity field tables) |
| `general`       | none of the above                                          | whatever fits, same principles     |

---

## Verify pass (before you call the doc done)

`plan-flow` step 2 lives here — review the doc as a skeptic:

- [ ] every arrow in §2 has a matching STEP in §3 (same story, no orphan hop)
- [ ] every error in an API response block appears in §3 logic and §8 edge cases
- [ ] every storage write / external call / side effect is named (table + op)
- [ ] trust boundaries are correct — who is allowed to compute money / hold
      credentials / be believed (webhook vs redirect)
- [ ] every uncertain decision is written in §11 Open Questions, and the risky
      ones are asked to the human **before** coding

If any item fails → fix the doc. Never output a flow you know is incomplete or
haven't challenged.

---

## Summary (mandatory, printed after writing the file — the ONLY brief part)

```text
── Sage Docs ─────────────────────────────────────
Language   · <chosen language>
Mode       · CREATE | UPDATE
Doc type   · <api-flow | backend-logic | frontend | architecture | user-journey | runbook | data-schema | general>
Output     · docs/<slug>.md
Systems    · <System A, System B, …>          ← repos/systems the flow spans
Sections   · <§ list>
Coverage   · <N> steps · <N> endpoints · <N> errors — all covered
Open Q     · <N> (asked: <the ones raised to the human>)
──────────────────────────────────────────────────
```
