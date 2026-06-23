---
applyTo: "docs/**"
---

# Sage Docs

When asked to run **sage-docs**, "document this", "generate docs for", or "update docs":

Role: `writer` — open `agents/sage/roles/role-writer.md` (create if missing).

**Speed rule:** Read all source + `agents/sage/docs/docs-style-template.md`
(+ existing HTML if updating) in one batch, then generate the full HTML in one
pass. Don't stop mid-way — except the one language question below.

**Language — one language only, never mixed.** Doc content is **English by
default**, but ask the user every time before generating (English / Thai /
Other). Write the **entire doc in that one language** — never mix Thai and
English prose or code-switch mid-sentence. The answer sets all prose +
`<html lang="...">`. Technical tokens (method/path/table/field/status/key/DTO)
keep their real names and don't count as mixing.

## Principles of good docs

1. **Answer-first** — open each section with one sentence on what it does.
2. **One idea per line** — each condition / branch / error on its own line.
3. **Concise = cut empty connectors, not conditions** — never drop a guard,
   error, or side effect.
4. **Concrete over abstract** — `422 { error: 'cart_empty' }` beats "return error".
5. **when → then** — write branches as "when X → do Y → return Z".
6. **Cover every exit** — one happy path + every error path.

Test: someone who never saw the code can re-implement every branch = complete ·
words deletable without losing meaning = not yet concise.

## Step 1 — Prepare

- **Ask doc language first** (mandatory, every time) — English default
- Detect slug; check if `docs/<slug>.html` exists
- **CREATE** (not found) → build new · **UPDATE** (found) → read it, preserve
  correct content, update changed, add missing, regenerate the whole file
- Log: `Mode: CREATE · docs/<slug>.html` or `Mode: UPDATE · ...`

## Step 2 — Analyze & classify

Extract: actors, endpoints (method + path), DTOs (real names), logic branches,
error paths (every 4xx/5xx), storage (table + READ/WRITE), cache (key/TTL/
invalidation), external calls (service + endpoint + retry), side effects,
frontend components (state, APIs called, middleware).

Doc types: `api-flow` · `backend-logic` · `frontend` · `architecture` ·
`user-journey` · `runbook` · `data-schema` · `general`

## Step 3 — Diagrams

**Same-story rule:** the diagram and the text in each section must tell the same
story — every diagram node maps 1:1 to the text below.

1. **Overview** — `80vh`, zoomable, all endpoints/components. Every node with a
   section below: `<a href="#slug">` for click-to-jump.
2. **Mini diagrams** — class `svg-diagram--mini` (~40vh), per endpoint/component,
   at the top of the section. For `api-flow`, `backend-logic`, `frontend` only.
   No extra JS — the shared `sage-docs.js` auto-wires every `.svg-diagram`; just
   repeat the block, no slug-suffixed IDs, buttons use `data-zoom="in|out|fit"`.

Inline SVG only (no Mermaid). All drawing inside `<g id="svg-content">`. The
shared JS transforms the `<g>` — never CSS transform on a wrapper (blurs at zoom).

Overview by type: `api-flow`/`backend-logic` → swimlane LR + flowchart TD per
endpoint · `frontend` → component tree LR + data-flow TD per component ·
`architecture` → graph LR · `user-journey` → swimlane LR · `runbook` → flowchart
TD · `data-schema` → ER grid.

Quality (mandatory): every participant role + tech · every request arrow full
method + path · every return arrow status + shape · storage nodes table + op ·
cache nodes key + TTL · external nodes service + endpoint · every error path a
leaf node with HTTP status · happy path leaf with response shape. Complex logic:
retry loop labeled `retry (max N)` · rollback branch in red · guard diamonds ·
parallel fork/join · conditional side-effect branch. Clean edges: connect
edge-midpoints (not corners) · orthogonal routing over diagonals · nodes on a
consistent grid · tight bounding box, no stray elements (JS auto-centers via getBBox).

## Step 4 — HTML structure

`docs/<slug>.html`, **referencing shared assets (do not inline)**:
`<link rel="stylesheet" href="../agents/sage/docs/sage-docs.css">` in `<head>`
and `<script src="../agents/sage/docs/sage-docs.js"></script>` as the last line
before `</body>`. Set `<html lang>` to the chosen language; write all prose in it.

Top-to-bottom: header · tldr-card · overview diagram (80vh) · sections per type
· footer.

TL;DR card (mandatory, right after header):

```html
<div class="tldr-card">
  <div class="tldr-label">TL;DR</div>
  <p>{2–3 sentences: what it does, who calls it, what it touches}</p>
  <div class="tldr-grid">
    <div class="tldr-stat"><span class="tldr-stat-label">Endpoints</span><span class="tldr-stat-value">{N}</span></div>
    <div class="tldr-stat"><span class="tldr-stat-label">Tables</span><span class="tldr-stat-value">{names}</span></div>
    <div class="tldr-stat"><span class="tldr-stat-label">Cache</span><span class="tldr-stat-value">{yes · key / no}</span></div>
    <div class="tldr-stat"><span class="tldr-stat-label">External</span><span class="tldr-stat-value">{services or none}</span></div>
  </div>
</div>
```

## Step 5 — Content by type

`api-flow` / `backend-logic`: per-endpoint `<section class="doc-section" id="{slug}">`
— mini diagram, request table (name the DTO), response table (2xx then every
4xx/5xx), logic flow, storage summary table. Logic format is flexible (pick:
short conditions-list / long conditions-list / steps-list / condition→outcome
table / paragraph) — but every storage op names table + op, every cache names
key + TTL, every external names service + endpoint, and the text matches the
diagram.

`frontend`: per-component `<section class="doc-section" id="{slug}">` — mini
diagram (user action → state → API → re-render) + conditions-list (renders, api
calls, state, middleware, children).

`architecture`/`user-journey`/`runbook`/`data-schema`: `<article class="doc-article">`
narrative — `<h2 id>` with `.h2-accent` per section, `.bridge` sentences linking
sections. No panel boxes.

Clickable SVG node: `<a href="#slug" style="cursor:pointer"><rect.../><text...>Label</text></a>`

## Step 6 — Completeness gate (before output)

- [ ] every overview node has a section below
- [ ] every error in the response table appears in the logic
- [ ] every storage/cache/external from Step 2 is documented
- [ ] every diagram node maps to text; every path ends in a clear outcome
- [ ] passes the principles (answer-first, concise, concrete)

If any fails → fill it in. Never output knowing something is missing.

## Summary (mandatory)

```text
── Sage Docs ─────────────────────────────────────
Language   · <chosen>
Mode       · CREATE | UPDATE
Doc type   · <type>
Diagram    · overview (80vh) + <N> mini diagrams
Output     · docs/<slug>.html
Sections   · <#slug1>, <#slug2>, ...
Coverage   · <N> endpoints · <N> errors · <N> storage ops — all covered
──────────────────────────────────────────────────
```
