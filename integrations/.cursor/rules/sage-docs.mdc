---
description: Sage Docs — turn any document into a styled HTML file with interactive SVG diagram
alwaysApply: false
---

When asked to run **sage-docs** or "document this" or "generate docs for":

Role: `writer` — open `agents/sage/roles/role-writer.md` (create if missing).

## Step 1 — Analyze & classify

Extract from the source: actors, steps, conditions, data stores, side effects,
API endpoints (method + path).

Pick a doc type:

- `api-flow` — frontend calling backend endpoints (exact methods + paths visible)
- `backend-logic` — server-side processing with conditions, storage, side effects
- `architecture` — system components and relationships
- `user-journey` — user steps through a product or feature
- `runbook` — operational procedure (setup, deploy, debug)
- `data-schema` — data models, entity relationships
- `general` — narrative/reference, no clear flow

## Step 2 — Diagram decision

If 3+ ordered steps, actors exchanging messages, or meaningful branches exist →
generate a diagram. Otherwise skip.

Use **inline SVG** — place all drawing inside `<g id="svg-content">`.
Apply pan/zoom by setting `group.setAttribute('transform', ...)` in JavaScript.
**Never** use CSS `transform` on a wrapper div — it rasterizes SVG at 1× then
scales pixels up, causing blurring. Native SVG group transform keeps everything
vector-sharp at any zoom level.

Read `agents/sage/docs/docs-style-template.md` §"Zoom/Pan JavaScript" and
§"HTML scaffold for zoomable diagram section" for the exact markup and JS.

SVG layout direction by doc type:

| Doc type | SVG layout |
| --- | --- |
| api-flow | left-to-right swim lanes |
| backend-logic | top-to-bottom nodes |
| architecture | left-to-right component boxes |
| user-journey | top-to-bottom or left-to-right |
| runbook | top-to-bottom nodes |
| data-schema | grid layout |

**Diagram quality rules:**

- `sequenceDiagram` style: name every actor with role + tech; show exact HTTP
  method + path on every arrow; show exact response status + shape on return;
  show every error case; show every branch
- `flowchart TD` style: start node = trigger with full detail; decision diamonds
  with literal conditions; storage nodes naming table + operation; side effect
  nodes named explicitly; leaf nodes showing HTTP status + response

## Step 3 — Write HTML to `docs/<slug>.html`

Generate a **self-contained file** — no external stylesheet.

1. Read `agents/sage/docs/docs-style-template.md`
2. Extract the CSS from the first ` ```css ` fenced code block
3. Paste it verbatim inside `<style>` in the HTML `<head>`

Do **not** create `docs/docs-style.css` or use `<link rel="stylesheet">`.

HTML structure (all types):

1. `<header>` — breadcrumb, type badge, domain badge, title, subtitle, date
2. `<section class="diagram-section">` — inline SVG with zoom/pan controls (if applicable)
3. `<section class="quick-ref">` — type-specific summary (endpoint table / component grid / etc.)
4. `<section class="doc-section">` × N — type-specific detail sections

**Per-type detail sections:**

`api-flow`: endpoint summary table → per-endpoint: request params + body schema,
response (2xx + errors), notes.

`backend-logic`: trigger → business logic conditions list → storage operations
table (op / store / what/when) → side effects table → error handling table.

`architecture`: components table → per-component detail → data flow → external
integrations table.

`user-journey`: actors table → steps list → decision points → success path →
failure/edge cases table.

`runbook`: prerequisites checklist → numbered steps → decision points → rollback
steps → verification checklist.

`data-schema`: per-entity field table → relationships table → constraints table.

## Summary (mandatory)

```
── Sage Docs ─────────────────────────────────────
**Doc type**   · <type>
**Diagram**    · inline SVG | none — <reason>
**Output**     · docs/<slug>.html
**CSS**        · inlined from agents/sage/docs/docs-style-template.md

**Sections written**
- <section name> — <brief description>

**Next** · open docs/<slug>.html in a browser to review
──────────────────────────────────────────────────
```
