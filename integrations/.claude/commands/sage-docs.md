# /sage-docs — create or update an HTML doc that humans actually read

Take source material (spec, README, PRD, code, meeting note) and produce
`docs/<slug>.html` — a continuous top-to-bottom narrative, no jumping around.

**Speed rule:** Read every file you need in one batch (docs-style-template +
source material + existing HTML if updating), then generate the full HTML in a
single pass. Do not stop to ask mid-way — **with one exception:** the doc
language (see §1), asked once before you start, every time. After that, no more
questions.

**Document language — one language only, never mixed.** Doc content is
**English by default**, but you must ask the user every time before generating
(see §1). Write the **entire doc in that one language** (Thai or English) — never
mix Thai and English prose, never code-switch mid-sentence. Set
`<html lang="...">` to match. Technical tokens (method, path, table, field,
status, key, DTO name) keep their real names and do not count as mixing.

---

## Principles of good docs (govern every section below)

The goal is **easy to read + complete conditions + concise** — these three
conflict if written badly. Use these principles to get all three at once:

1. **Answer-first** — open each section with one sentence saying what it does,
   before the details. The reader needs the big picture before the edge cases.
2. **One idea per line** — each condition / branch / error on its own line.
   Don't cram multiple logic steps into one sentence — complete because it's
   clearly separated, not because it's long.
3. **Concise = cut empty connectors, not conditions** — remove "in the case
   that", "which will then", "normally" — but never remove a guard, error, or
   side effect. Every condition stays; it's just written shorter.
4. **Concrete over abstract** — `422 { error: 'cart_empty' }` beats "return
   error if invalid"; `UPDATE orders SET status='paid'` beats "save the status"
   — use real table/field/status/key names.
5. **Show conditions as when → then** — write every branch as "when X → do Y →
   return Z", not loose prose. The reader must be able to trace each path
   top-to-bottom.
6. **Cover every exit** — every path ends in a clear outcome: one happy path +
   every error path. If the response table has 422 and 409, the logic must show
   both.

> **The test:** if someone who has never seen the code can re-implement every
> branch correctly from the doc = complete · if you can delete words without
> losing meaning = not yet concise enough.

---

## Workflow

### 1 — Prepare

**Ask doc language (mandatory — do this first, every time):** Use
AskUserQuestion to ask which language the docs should be in, before reading
source or writing anything. Never skip, never assume — even if you asked in a
previous session.

- options: **English (default/recommended)** · Thai · Other
- the answer sets the language of all prose + `<html lang="...">`
- technical tokens (method/path/table/field/status/key/DTO) always stay as
  their real names

**Load role:** open `agents/sage/roles/role-writer.md` → adopt immediately.
If missing, create it (persona: loves making complex systems clear at a glance).

**Detect mode:**

- derive slug from the document title (kebab-case)
- check whether `docs/<slug>.html` exists
- **CREATE** — file doesn't exist → build new from source
- **UPDATE** — file exists → read it, preserve content that's still correct,
  update what changed, add what's missing, regenerate the whole file

Log before proceeding:
`Mode: CREATE · docs/<slug>.html` or `Mode: UPDATE · docs/<slug>.html · changed: <list>`

---

### 2 — Analyze source and classify

**Read everything in one batch:** docs-style-template.md + all source.

Extract from the source:

| What to find        | Example                                                                |
| ------------------- | ---------------------------------------------------------------------- |
| Actors              | user, frontend service, backend service, DB, queue, external API       |
| Endpoints           | `POST /api/v1/orders` — full method + path                             |
| DTOs                | `CreateOrderDto`, `OrderResponseDto` — real names from code            |
| Logic branches      | validate → check stock → reserve → charge — every if/else, every guard |
| Error paths         | every 4xx/5xx — when it happens, what it returns                       |
| Storage             | table name, READ or WRITE, under what condition                        |
| Cache               | Redis key pattern, TTL, invalidation trigger                           |
| External calls      | service name, endpoint called, timeout/retry                           |
| Side effects        | event published, email sent, webhook fired                             |
| Frontend components | component name, state held, APIs called, middleware                    |

**Classify doc type:**

| Type            | Pick when                                                                   |
| --------------- | --------------------------------------------------------------------------- |
| `api-flow`      | source shows frontend/client calling backend endpoints                      |
| `backend-logic` | source describes server-side processing — conditions, storage, side effects |
| `frontend`      | source describes component tree, state flow, API calls from the UI          |
| `architecture`  | source describes system components and their relationships                  |
| `user-journey`  | source describes steps a user takes through a feature                       |
| `runbook`       | source is an operational procedure — setup, deploy, debug                   |
| `data-schema`   | source describes data models, entity relationships                          |
| `general`       | none of the above                                                           |

---

### 3 — Plan the diagrams

**First rule (mandatory):** the diagram and the text in each section must tell
**the same story** — the diagram shows it, the text (list / table / paragraph
per §5) explains the detail. If the diagram has branches A → B → C, the text
below must explain all three — each diagram node maps 1:1 to the text.

**Every doc can have two levels:**

**Overview diagram** (80vh, zoomable, full width)

- shows all endpoints or components at a glance
- every node that has a section below must be wrapped in `<a href="#slug">` so a
  click jumps to it
- use inline SVG only — no Mermaid, no CSS transform on a wrapper div (blurs at
  zoom) → use `group.setAttribute('transform', …)` only

**Mini diagrams** (40vh, class `svg-diagram--mini`, per endpoint/component)

- placed at the top of the section, always before the request/response tables
- used for `api-flow`, `backend-logic`, `frontend` only
- no extra JS — the shared `sage-docs.js` auto-wires every `.svg-diagram`; just
  repeat the `.svg-diagram` block, no slug-suffixed IDs, buttons use `data-zoom`

**Overview style by doc type:**

| Type            | Overview                            | Mini per item              |
| --------------- | ----------------------------------- | -------------------------- |
| `api-flow`      | swimlane LR — participants + arrows | flowchart TD per endpoint  |
| `backend-logic` | flowchart TD of the whole module    | flowchart TD per endpoint  |
| `frontend`      | component tree LR                   | data flow TD per component |
| `architecture`  | graph LR — components + edges       | none                       |
| `user-journey`  | swimlane LR                         | none                       |
| `runbook`       | flowchart TD                        | none                       |
| `data-schema`   | ER grid                             | none                       |

**Diagram quality — all mandatory:**

For swimlane (LR):

- every participant: role + tech → `Frontend (Next.js)`, `DB (PostgreSQL)`
- every request arrow: `POST /api/v1/orders` — full method + path
- every return arrow: `201 { order_id, status }` — status + shape
- solid line = request, dashed line = response
- DB query shows table + operation: `SELECT * FROM orders WHERE id=$1`

For flowchart TD:

- Start node: trigger with full detail → `POST /api/v1/payments\n{order_id, amount}`
- Decision diamond: literal condition → `order.status == 'pending'?`
- Storage node: table + op → `UPDATE orders SET status='paid', paid_at=NOW()`
- Cache node: key + TTL → `Redis SET order:{id} TTL=300s`
- External call node: service + endpoint → `Stripe POST /v1/charges`
- Side effect node: `Publish OrderPaid → payments.events`
- Every error path needs a leaf node: `422 { error: 'insufficient_stock' }`
- Happy path leaf: `200 OK { order_id, total, status: 'confirmed' }`

**Drawing complex logic — extra rules:**

- **Retry logic:** draw a loop arrow back up, labeled `retry (max 3)`
- **Compensation / rollback:** draw a separate branch in red (`#ar-red` or stroke var(--red))
- **Guard clause:** a diamond before the main logic — if it fails → error leaf node immediately
- **Parallel ops:** draw a fork (two lines) then join back
- **Conditional side effect:** branch off the main path to the side-effect node

**Clean edges (avoid the "weird lines" look):**

- Connect from a node's **edge midpoint** (parent bottom-center → child
  top-center), never from a corner. Compute each node's true center.
- Prefer **orthogonal routing** (vertical then horizontal) over long diagonals;
  a shared bus line + short drops beats many diagonals fanning from one point.
- Lay nodes on a **consistent grid** (equal columns, aligned rows) so edges stay
  short and parallel — misaligned nodes are what make lines look off.
- Keep the drawing's bounding box tight — no stray off-canvas elements or huge
  margins. The shared JS auto-centers via `getBBox()`; one stray element inflates
  the box and pushes everything off-center.

---

### 4 — HTML structure

**Output file:** `docs/<slug>.html` — **reference the shared assets, do not
inline CSS/JS.** The stylesheet and zoom/pan JS live in `agents/sage/docs/`.

```html
<head>
  …
  <link rel="stylesheet" href="../agents/sage/docs/sage-docs.css" />
</head>
<body>
  …
  <script src="../agents/sage/docs/sage-docs.js"></script>
  <!-- last line before </body> -->
</body>
```

The JS auto-wires **every** `.svg-diagram` on the page (overview + all mini
diagrams) — no inline `<style>`, no per-diagram script, no slug-suffixed IDs.
Buttons use `data-zoom="in|out|fit"`. If `agents/sage/docs/sage-docs.css|js`
don't exist yet, copy them from this repo first.

Set `<html lang="...">` to the language chosen in §1 (`en` for English, `th` for
Thai) and write all prose in that language.

**The document must always read top-to-bottom:**

```text
<header>          breadcrumb · badges · title · subtitle · date
<div.tldr-card>   TL;DR 2–3 sentences + stat grid
<section.diagram-section>  overview diagram (80vh)
<article/sections>         content per type — see §5
<footer>
```

**TL;DR card (mandatory, always right after header):**

```html
<div class="tldr-card">
  <div class="tldr-label">TL;DR</div>
  <p>
    {2–3 sentences in chosen language: what this module does, who calls it, what
    it touches}
  </p>
  <div class="tldr-grid">
    <div class="tldr-stat">
      <span class="tldr-stat-label">Endpoints</span
      ><span class="tldr-stat-value">{N}</span>
    </div>
    <div class="tldr-stat">
      <span class="tldr-stat-label">Tables</span
      ><span class="tldr-stat-value">{table names}</span>
    </div>
    <div class="tldr-stat">
      <span class="tldr-stat-label">Cache</span
      ><span class="tldr-stat-value">{yes · key pattern / no}</span>
    </div>
    <div class="tldr-stat">
      <span class="tldr-stat-label">External</span
      ><span class="tldr-stat-value">{services or none}</span>
    </div>
  </div>
</div>
```

---

### 5 — Content by doc type

#### `api-flow` and `backend-logic` — per-endpoint panel

Use `<section class="doc-section">` (panel box), one per endpoint — each is a
self-contained unit.

```html
<section
  id="{method-path-slug}"
  class="doc-section"
  style="margin-bottom:32px; scroll-margin-top:24px;"
>
  <h2>
    <span class="badge badge-method badge-{verb}">{VERB}</span>
    &nbsp;<code>{/api/path}</code>
    <span
      style="margin-left:auto; font-size:0.78rem; color:var(--muted); font-weight:400"
      >{purpose}</span
    >
  </h2>

  <!-- Mini diagram: flowchart TD showing the full request journey -->
  <!-- MUST show: auth check → validate DTO → every guard → main logic →
       storage ops → cache ops → external calls → side effects → response -->
  <!-- MUST show: every error branch with its HTTP status as a leaf node -->
  <div class="diagram-container" style="margin:16px 24px 0;">
    <div class="svg-diagram svg-diagram--mini">
      <!-- controls (buttons data-zoom="in|out|fit") + <svg> with <g id="svg-content"> -->
      <!-- no per-diagram script — shared sage-docs.js wires it automatically -->
    </div>
  </div>

  <!-- Request — name the DTO class above the table -->
  <!-- Response — 2xx row first, then every 4xx/5xx row -->

  <!-- Logic flow — the text MUST mirror the diagram above -->
  <!-- Each item maps 1:1 to a node in the mini diagram -->
  <!-- Include: cache hit/miss, DB ops (table + op), external calls, retry logic -->

  <!-- Storage summary table: Store | Op | Table/Key | Condition -->
  <!-- One row per: DB read, DB write, cache get, cache set, external call -->
</section>
```

**Logic documentation — pick the format that fits the endpoint:**

No fixed format — choose based on what the endpoint actually has:

| What the endpoint has                  | Fitting format                                        |
| -------------------------------------- | ----------------------------------------------------- |
| simple CRUD (validate → save → return) | short `conditions-list`, 3–4 items                    |
| many branches, retry, compensation     | long `conditions-list` + diagram emphasizing branches |
| a clear sequential process             | `steps-list` with step numbers                        |
| logic depending on multiple states     | table (condition → outcome)                           |
| internal utility, no auth/cache        | a short paragraph instead of a list                   |

**Example conditions-list** (use when logic has several guards / branches):

```html
<ul class="conditions-list">
  <li class="condition-item">
    <span class="condition-when">auth</span>
    <span class="condition-then"
      >Verify JWT → extract <code>userId</code> → if invalid → 401</span
    >
  </li>
  <li class="condition-item">
    <span class="condition-when">cache</span>
    <span class="condition-then"
      >Redis GET <code>cart:{userId}</code> — hit: use it, miss: SELECT from
      <code>cart_items</code></span
    >
  </li>
  <li class="condition-item">
    <span class="condition-when">guard</span>
    <span class="condition-then"
      >if cart is empty → 422 <code>{ error: 'cart_empty' }</code></span
    >
  </li>
  <li class="condition-item">
    <span class="condition-when">external</span>
    <span class="condition-then"
      >POST Stripe /v1/charges — on fail → retry max 3 → UPDATE
      <code>orders</code> SET status='failed'</span
    >
  </li>
  <li class="condition-item">
    <span class="condition-when">side effect</span>
    <span class="condition-then"
      >Publish <code>OrderCreated</code> → <code>orders.events</code></span
    >
  </li>
</ul>
```

**Rules for every format:**

- include only what the endpoint actually has — don't force an auth row onto a public endpoint
- every storage op must name table + READ/WRITE
- every cache must name key pattern + TTL
- every external call must name service + endpoint + retry/timeout if any
- the logic written down must match the diagram above — same story

---

#### `frontend` — per-component panel

```html
<section
  id="{component-slug}"
  class="doc-section"
  style="margin-bottom:32px; scroll-margin-top:24px;"
>
  <h2>
    {ComponentName}
    <span style="color:var(--muted); font-weight:400; font-size:0.85rem"
      >— {Page/Feature}</span
    >
  </h2>

  <!-- Mini diagram: data/event flow — user action → state → API → re-render -->
  <!-- Show: props received, state held, API calls triggered, child components -->
  <div class="diagram-container" style="margin:16px 24px 0;">
    <div class="svg-diagram svg-diagram--mini">
      <!-- controls (buttons data-zoom) + <svg> with <g id="svg-content"> -->
    </div>
  </div>

  <div style="padding:16px 24px 24px;">
    <ul class="conditions-list">
      <li class="condition-item">
        <span class="condition-when">renders</span>
        <span class="condition-then"
          >{what data it shows, where it comes from}</span
        >
      </li>
      <li class="condition-item">
        <span class="condition-when">api calls</span>
        <span class="condition-then"
          >{method + path + when → e.g. GET /api/v1/orders on mount}</span
        >
      </li>
      <li class="condition-item">
        <span class="condition-when">state</span>
        <span class="condition-then"
          >{local useState vs store — key fields}</span
        >
      </li>
      <li class="condition-item">
        <span class="condition-when">middleware</span>
        <span class="condition-then"
          >{axios interceptors, auth guard, error boundary}</span
        >
      </li>
      <li class="condition-item">
        <span class="condition-when">children</span>
        <span class="condition-then">{child components — what each does}</span>
      </li>
    </ul>
  </div>
</section>
```

---

#### `architecture`, `user-journey`, `runbook`, `data-schema` — narrative article

Use `<article class="doc-article">`, no panel box — content flows as a narrative.

```html
<article class="doc-article">
  <p>{intro connecting the overview diagram to the details below}</p>

  <h2 id="{section-slug}">
    <span class="h2-accent" style="background:var(--mint)"></span>
    {Section title}
  </h2>
  <p>{narrative description — tell the story, not just a list}</p>
  <!-- relevant table/list/code -->
  <p class="bridge">{one sentence linking this section to the next}</p>

  <h2 id="{next-section-slug}">
    <span class="h2-accent" style="background:var(--amber)"></span>
    {Next section title}
  </h2>
  <!-- and so on -->
</article>
```

`architecture`: intro → per-component (name, responsibility, tech, exposes, consumes)
`user-journey`: intro → steps-list → decision points → success/failure paths
`runbook`: intro → prerequisites → steps-list → rollback → verification callouts
`data-schema`: intro → per-entity field table → relationships table → constraints table

---

### 6 — Clickable SVG nodes

Every node in the overview diagram that has a section below must be wrapped like:

```svg
<a href="#section-slug" style="cursor:pointer">
  <rect x="..." y="..." width="..." height="..." rx="6"
        fill="rgba(113,215,255,0.12)" stroke="#71d7ff" stroke-width="1.5"/>
  <text x="..." y="..." fill="#71d7ff" font-size="11" text-anchor="middle">
    POST /api/v1/orders
  </text>
</a>
```

Plain HTML anchor inside SVG — no JS needed, just `href="#slug"`.

---

### 7 — Completeness gate (before output)

Before writing the file, check nothing from the §2 extraction was dropped:

- [ ] every endpoint/component in the overview diagram has a section below
- [ ] every error in the response table appears in the logic flow (422 in table → 422 in logic)
- [ ] every storage / cache / external call extracted in §2 is documented
- [ ] every diagram node maps to text (no orphan node without explanation)
- [ ] every path in the diagram ends in a clear outcome (no line that goes nowhere)
- [ ] passes the §"Principles of good docs" — answer-first, concise, concrete

If any item fails → go back and fill it in. Never output knowing something is missing.

### 8 — Summary (mandatory)

```text
── Sage Docs ─────────────────────────────────────
Language   · <chosen language>
Mode       · CREATE | UPDATE
Doc type   · <type>
Diagram    · overview (80vh) + <N> mini diagrams
Output     · docs/<slug>.html
Sections   · <#slug1>, <#slug2>, ...
Coverage   · <N> endpoints · <N> errors · <N> storage ops — all covered
──────────────────────────────────────────────────
```
