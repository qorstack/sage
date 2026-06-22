# /sage-docs — turn any document into a human-readable HTML file with diagram

Take a source document (spec, README, meeting note, PRD, code comment) and
produce a polished HTML file that:

1. **Detects** whether the content can be visualized as a flow/sequence/component
   diagram — if yes, renders a Mermaid diagram at the top with full technical detail
2. **Classifies** the content into a doc type and uses the matching HTML pattern
3. **Writes** a styled HTML file to `docs/` using the team's shared stylesheet

Run this whenever a team member needs a document that a human will actually open
and read — not AI knowledge, but shareable documentation.

---

## Role (fixed — `writer`)

Open `agents/sage/roles/role-writer.md` before starting:

- **Found** → read and adopt as-is. Output: `Role: writer [loaded]`
- **Missing** → create it now, output: `Role: writer [created]`

Default Ikigai if creating:

- Loves — making complex systems understandable at a glance
- Good at — analyzing content structure, choosing the right diagram type,
  writing docs that engineers and non-engineers can both use
- Team needs — clear documentation that doesn't require source-diving to understand
- Worth it — a well-written doc with a diagram is read; a wall of text is not

---

## Step 1 — Analyze the source material

Read the source material provided by the user. Extract:

- **Actors** — who/what initiates, processes, or receives (users, services, APIs,
  databases, queues, external systems)
- **Steps** — ordered sequence of operations
- **Conditions** — if/else branches, guard clauses, error cases
- **Data stores** — databases, caches, files, queues — and what gets read/written
- **Side effects** — emails, events, webhooks, external API calls, notifications
- **API endpoints** — HTTP method + path (e.g. `POST /api/v1/orders`)

Then classify into one doc type:

| Type | When to pick |
| --- | --- |
| `api-flow` | Document shows frontend/client calling backend endpoints — extract exact methods + paths |
| `backend-logic` | Document describes server-side processing — conditions, storage, side effects |
| `architecture` | Document describes system components and their relationships |
| `user-journey` | Document describes steps a user takes through a product or feature |
| `runbook` | Document is an operational procedure — setup, deploy, debug, rollback |
| `data-schema` | Document describes data models, entity relationships, field definitions |
| `general` | None of the above — narrative, reference, or ADR without a clear flow |

State your classification:

```text
Doc type: <type>
Diagram: yes — <mermaid-type> | no — <reason>
```

---

## Step 2 — Generate the diagram (if applicable)

**Diagram decision rule:** If you identified 3+ ordered steps, actors exchanging
messages, or a meaningful branch (condition → different outcome), generate a
diagram. If the content is a flat list, a pure reference, or fewer than 3 steps,
skip the diagram and note why.

Choose the Mermaid diagram type:

| Doc type | Mermaid diagram |
| --- | --- |
| `api-flow` | `sequenceDiagram` |
| `backend-logic` | `flowchart TD` |
| `architecture` | `graph LR` |
| `user-journey` | `sequenceDiagram` or `flowchart TD` |
| `runbook` | `flowchart TD` |
| `data-schema` | `erDiagram` or `classDiagram` |

**Diagram quality rules — these are mandatory, not optional:**

For `sequenceDiagram` (api-flow, user-journey):

- Name every participant with both role and technology: `participant FE as Frontend (Next.js)`
- Show the exact HTTP method + path on every request arrow: `FE->>BE: POST /api/v1/orders`
- Show the exact response status + shape on return arrows: `BE-->>FE: 201 { order_id, total, status }`
- Use `alt / else / opt` blocks for every conditional branch
- Show database queries as actual SQL-lite notation: `BE->>DB: SELECT * FROM carts WHERE id = $cart_id`
- Show every error case with its HTTP status code

For `flowchart TD` (backend-logic, runbook):

- Start node = trigger with full detail: `A([Trigger: POST /api/v1/payments\nBody: order_id, amount])`
- Every decision diamond must show the condition literally: `D{order.status == 'pending'?}`
- Every storage operation must name the table + operation: `G[UPDATE orders\nSET status='paid', paid_at=NOW()]`
- Every side effect must be named: `H[Publish event: OrderPaid\nQueue: payments.events]`
- Leaf nodes must show the HTTP response or outcome: `Z([200 OK\n{ payment_id, status: 'paid' }])`

For `graph LR` (architecture):

- Group related nodes with `subgraph`
- Name every edge with the protocol/method: `FE -->|REST /api| BE`
- Use distinct node shapes: `[Service]` `[(Database)]` `>Queue]` `([External API])`

For `erDiagram` (data-schema):

- Show all relationships with cardinality
- Include at least the primary key and 3–5 key fields per entity
- Name relationship verbs (PLACES, CONTAINS, BELONGS_TO)

---

## Step 3 — Build the HTML file

### Output location

```text
docs/<slug>.html
```

Where `<slug>` is kebab-case derived from the document title
(e.g. `checkout-payment-flow.html`, `auth-service-architecture.html`).

### Self-contained HTML — inline the CSS

Every generated doc is a **single self-contained file** — no external stylesheet.

1. Read `agents/sage/docs/docs-style-template.md`
2. Extract the CSS from the first ` ```css ` fenced code block
3. Paste it verbatim inside `<style>` in the HTML `<head>`

Do **not** write a `docs/docs-style.css` file or use `<link rel="stylesheet">`.

### Diagram approach — inline SVG, not Mermaid

Use an **inline `<svg>`** with all drawing inside `<g id="svg-content">`.
Apply pan/zoom by setting `group.setAttribute('transform', …)` in JavaScript.

**Never** use CSS `transform` on a wrapper div — it rasterizes at 1× then scales
the pixels up, causing blurring at zoom. Native SVG group transform keeps
everything vector-sharp at any zoom level.

Read `agents/sage/docs/docs-style-template.md` §"Zoom/Pan JavaScript" and
§"HTML scaffold for zoomable diagram section" for the exact markup and JS to use.

Use the diagram type table from Step 2 to decide the SVG layout direction:

- `sequenceDiagram` style → left-to-right swim lanes in SVG
- `flowchart TD` style → top-to-bottom nodes in SVG
- `graph LR` style → left-to-right component boxes in SVG
- `erDiagram` / `classDiagram` style → grid layout in SVG

### HTML shell

Every doc uses this shell (fill in `{…}` placeholders):

```html
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Title} — Sage Docs</title>
  <style>
{paste full CSS from agents/sage/docs/docs-style-template.md here}
  </style>
</head>
<body>
<div class="doc-wrapper">

  <header class="doc-header">
    <nav class="breadcrumb">
      <a href="./index.html">Docs</a>
      <span class="breadcrumb-sep">›</span>
      <span>{Domain}</span>
      <span class="breadcrumb-sep">›</span>
      <span>{Title}</span>
    </nav>
    <div class="doc-meta">
      <span class="badge badge-{type}">{type-label}</span>
      <span class="badge badge-domain">{domain}</span>
    </div>
    <h1>{Title}</h1>
    <p class="doc-subtitle">{one-sentence description}</p>
    <p class="doc-date">Generated {date} · sage-docs</p>
  </header>

  <!-- DIAGRAM SECTION (include only if diagram was generated) -->
  <!-- Use the SVG scaffold from docs-style-template.md -->
  <section class="diagram-section">
    <h2>Overview Diagram</h2>
    <div class="diagram-label">{label — e.g. "Top-to-bottom · Trigger → Logic → Output"}</div>
    <div class="diagram-container">
      <div class="svg-diagram" id="svg-zoom-container">
        <div class="diagram-controls">
          <button onclick="diagramZoomIn()" title="Zoom in">+</button>
          <div class="sep"></div>
          <button onclick="diagramZoomOut()" title="Zoom out">−</button>
          <div class="sep"></div>
          <button onclick="diagramZoomFit()" title="Reset" style="font-size:11px">fit</button>
          <div class="sep"></div>
          <span class="zoom-level" id="zoom-label">100%</span>
        </div>
        <svg id="svg-canvas" width="100%" height="100%"
             xmlns="http://www.w3.org/2000/svg"
             style="font-family:'Inter',system-ui,sans-serif; display:block;">
          <defs>
            <marker id="ar-mint"   viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto"><polygon points="0,0 10,4 0,8" fill="#68d99b" opacity="0.8"/></marker>
            <marker id="ar-amber"  viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto"><polygon points="0,0 10,4 0,8" fill="#f0c45c" opacity="0.7"/></marker>
            <marker id="ar-violet" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto"><polygon points="0,0 10,4 0,8" fill="#a98cff" opacity="0.7"/></marker>
            <marker id="ar-cyan"   viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto"><polygon points="0,0 10,4 0,8" fill="#71d7ff" opacity="0.8"/></marker>
          </defs>
          <g id="svg-content">
            {SVG nodes, lines, text — detailed per doc type}
          </g>
        </svg>
        <div class="diagram-hint">scroll to zoom · drag to pan</div>
      </div>
    </div>
    <p class="diagram-caption">{one-line caption}</p>
  </section>

  <!-- QUICK REFERENCE (always present, content varies by type) -->
  <section class="quick-ref">
    <h2>Quick Reference</h2>
    {type-specific quick-ref content — see Step 4}
  </section>

  <!-- DETAIL SECTIONS (type-specific — see Step 4) -->
  {detail sections}

  <footer class="doc-footer">
    <span class="sage-brand">Sage Docs</span>
    <span>Generated by sage-docs · {date}</span>
  </footer>

</div>
{paste zoom/pan JS from agents/sage/docs/docs-style-template.md here, inside <script>}
</body>
</html>
```

---

## Step 4 — Type-specific content patterns

Use these patterns exactly. Each section is a `<section class="doc-section">`.

### api-flow

**Quick ref** — endpoint summary table:

```html
<div class="table-wrap">
  <table>
    <thead><tr>
      <th>Method</th><th>Endpoint</th><th>Auth</th><th>Purpose</th>
    </tr></thead>
    <tbody>
      <tr>
        <td><span class="badge badge-method badge-post">POST</span></td>
        <td><code>/api/v1/orders</code></td>
        <td>JWT Bearer</td>
        <td>Create a new order from cart</td>
      </tr>
    </tbody>
  </table>
</div>
```

**Detail sections** (one `<section class="doc-section">` per endpoint):

1. Endpoint header (method badge + path)
2. Request — URL params table, query params table, request body schema table
3. Response — 2xx table, 4xx/5xx error table (code, condition, body)
4. Notes / edge cases

### backend-logic

**Quick ref** — trigger + branch summary:

```html
<div class="quick-ref-grid">
  <div class="quick-ref-item">
    <div class="quick-ref-label">Trigger</div>
    <div class="quick-ref-value">POST /api/v1/payments</div>
  </div>
  <div class="quick-ref-item">
    <div class="quick-ref-label">Main branches</div>
    <div class="quick-ref-value">3 (pending → success, already paid, cancelled)</div>
  </div>
  ...
</div>
```

**Detail sections:**

1. **Trigger** — what starts this flow (HTTP endpoint, cron expression, event name)
2. **Business Logic** — conditions list using `.conditions-list` + `.condition-item` markup
3. **Storage Operations** — table: operation (READ/WRITE), store name, what/when
4. **Side Effects** — table: effect, trigger condition, detail
5. **Error Handling** — table: error case, HTTP status, response body, logged?

### architecture

**Quick ref** — components grid (name, type, tech, responsibility).

**Detail sections:**

1. **Components** — one subsection per component: name, responsibility, tech, exposes (API/events)
2. **Data Flow** — narrative description with inline `<code>` for protocols
3. **External Integrations** — table: service name, purpose, auth method, direction

### user-journey

**Quick ref** — actors + entry points.

**Detail sections:**

1. **Actors** — table: actor, description, entry point
2. **Journey Steps** — `.steps-list` + `.step-item` markup
3. **Decision Points** — conditions list
4. **Success Path** — what the user sees/gets
5. **Failure/Edge Cases** — table: case, what happens, recovery

### runbook

**Quick ref** — prerequisites + estimated time grid.

**Detail sections:**

1. **Prerequisites** — checklist (unordered list)
2. **Steps** — `.steps-list` with `.step-item` (number badge + title + detail)
3. **Decision Points** — conditions list
4. **Rollback** — numbered steps
5. **Verification** — checklist of things to confirm success

### data-schema

**Quick ref** — entity list grid.

**Detail sections:**

1. Per entity: field table (name, type, constraints, description)
2. **Relationships** — table: from → to, type (1:N, M:N), join key
3. **Constraints / Validations** — table: field, rule, enforced at (DB/app/API)

### general

No diagram unless the AI finds a clear flow in the content.

**Detail sections:** derive from the source material's own structure.
Use `.callout` boxes for warnings, important notes, or key decisions.

---

## Step 5 — Summary (mandatory — a response without this is incomplete)

Output as **plain markdown** (no code fence):

```markdown
── Sage Docs ─────────────────────────────────────
**Doc type**   · <type>
**Diagram**    · <mermaid-type> | none — <reason>
**Output**     · `docs/<slug>.html`
**CSS** · inlined from agents/sage/docs/docs-style-template.md

**Sections written**
- <section name> — <brief description>

**Next** · open docs/<slug>.html in a browser to review
──────────────────────────────────────────────────
```
