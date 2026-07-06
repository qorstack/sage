# /sage-docs — create or update a Markdown flow doc humans actually read

Take source material (spec, README, PRD, code, meeting note) and produce
`docs/<slug>.md` — a **plain Markdown** flow doc that reads top-to-bottom: actors
→ end-to-end ASCII overview → step-by-step → API spec → edge cases → security →
build checklist → open questions. No HTML, no CSS, no JS, no browser.

**The style-guide is the source of truth:** read
[`agents/sage/docs-style-template.md`](agents/sage/docs-style-template.md)
before generating — it defines the skeleton, the ASCII-flow rules, and the
completeness bar. This command is the workflow around it.

**Speed rule:** Read everything you need in one batch (the style-guide + source
material + the existing `.md` if updating), then generate the full doc in a
single pass. Do not stop mid-way — **with one exception:** the doc language (§1),
asked once before you start, every time. After that, no more questions **unless
the verify pass (§6) surfaces a genuine doubt** — then ask.

**Write in full — never abbreviate the doc.** The doc is the deliverable, not a
summary of one. The only brief part is the closing summary block (§7). Never cut
a guard, an error path, or a side effect to save space.

---

## Principles of good docs (govern every section)

Easy to read **+** complete conditions **+** concise — all three at once:

1. **Answer-first** — open each section with one sentence on what it does.
2. **One idea per line** — each condition / branch / error on its own line.
3. **Concise = cut connectors, not conditions** — drop "in the case that";
   keep every guard, error, and side effect.
4. **Concrete over abstract** — `422 { error: 'cart_empty' }` beats "return an
   error"; `UPDATE orders SET status='paid'` beats "save the status".
5. **when → then** — write branches as "when X → do Y → return Z".
6. **Cover every exit** — one happy path + every error path.

> **The test:** someone who never saw the code can re-implement every branch from
> the doc = complete · you can delete words without losing meaning = not concise
> enough yet.

---

## Workflow

### 1 — Prepare

**Ask doc language first (mandatory, every time).** Use AskUserQuestion before
reading source or writing anything: **English (default/recommended)** · Thai ·
Other. The answer sets the language of all prose. Never mix two languages;
technical tokens (method/path/table/field/status/key/DTO) keep their real names.

**Load role:** open `agents/sage/roles/role-writer.md` → adopt immediately. If
missing, create it (persona: loves making complex systems clear at a glance).

**Detect mode** (derive slug from the title, kebab-case):

- **CREATE** — `docs/<slug>.md` doesn't exist → build new from source.
- **UPDATE** — it exists → read it, preserve what's still correct, update what
  changed, add what's missing, regenerate the whole file.

Log: `Mode: CREATE · docs/<slug>.md` or `Mode: UPDATE · docs/<slug>.md · changed: <list>`

### 2 — Analyze source and classify

**Read in one batch:** the style-guide + all source. Extract:

| What to find     | Example                                                      |
| ---------------- | ------------------------------------------------------------ |
| Actors / systems | user, website, backend service, payment-service, DB, gateway |
| Endpoints        | `POST /api/TrnSubmits/{id}/pay` — full method + path         |
| DTOs / shapes    | request/response JSON — real field names from code           |
| Logic branches   | validate → guard → main → storage → external → side effect   |
| Error paths      | every 4xx/5xx — when it happens, what it returns             |
| Storage          | table + READ/WRITE, under what condition                     |
| External calls   | service + endpoint + timeout/retry                           |
| Side effects     | event published, webhook fired, email sent                   |
| Trust boundaries | who computes money / holds credentials / is believed         |

**Classify the doc type** (shapes the section set — see the style-guide table):
`api-flow` · `backend-logic` · `frontend` · `architecture` · `user-journey` ·
`runbook` · `data-schema` · `general`.

**Note the systems/repos the flow spans** — in a multi-repo workspace, every step
and endpoint must name which system owns it.

### 3 — Build the flow (write the doc)

Follow the skeleton in the style-guide, top-to-bottom:

1. **Title + blockquote** — feature, system scope, "refs real code as of `<date>`".
2. **§1 Actors & Systems** — table + trust-boundary bullets.
3. **§2 End-to-end overview** — ONE ASCII flow (fenced code block) of the whole
   thing, following the style-guide's spine rules (name the system at each hop,
   real calls on the arrows, `├─(A)`/`└─(B)` branches), then a **Key/หัวใจ** line.
4. **§3 Step-by-step** — one `### STEP n` per hop in the overview; each names its
   system(s), the APIs (mark exists vs must-build), concrete actions, business
   rules with real numbers.
5. **§5 API spec** — grouped by system; per endpoint a `jsonc` Request +
   Response (2xx and every error), Guard, Side effect, Idempotency.
6. Remaining sections that apply: **§4 state lifecycle · §6 status lifecycle ·
   §7 data model · §8 edge cases · §9 security · §10 build checklist**.

The ASCII overview and the step text must tell **the same story** — every hop in
the diagram has a step below it, and vice versa.

### 4 — Verify the flow ("should it really be this way?")

Before finishing, review the doc as a skeptic, not its author (this is
`plan-flow` step 2):

- check each step against the real code/schema
- hunt weak points: wrong trust boundary, missed error path, a step that
  contradicts an existing rule, a simpler route
- write **§11 Open Questions** for everything genuinely uncertain
- **ask the human now** for the risky/ambiguous ones — do not paper over a doubt

### 5 — Completeness gate (before writing the file)

- [ ] every hop in the §2 overview has a §3 step (same story, no orphan)
- [ ] every error in an API response block appears in §3 logic and §8 edge cases
- [ ] every storage write / cache / external call / side effect is named
- [ ] trust boundaries are correct and stated
- [ ] every uncertainty is in §11, and the risky ones were asked
- [ ] passes the principles — answer-first, concise, concrete

If any item fails → fill it in. Never output knowing something is missing.

### 6 — Write `docs/<slug>.md`

Plain Markdown. ASCII diagrams in fenced code blocks. Set nothing HTML. Match the
depth of the reference flow doc — complete, not summarized.

### 7 — Summary (mandatory — the ONLY brief part)

```text
── Sage Docs ─────────────────────────────────────
Language   · <chosen language>
Mode       · CREATE | UPDATE
Doc type   · <type>
Output     · docs/<slug>.md
Systems    · <System A, System B, …>
Sections   · <§ list>
Coverage   · <N> steps · <N> endpoints · <N> errors — all covered
Open Q     · <N> (asked: <the ones raised to the human>)
──────────────────────────────────────────────────
```
