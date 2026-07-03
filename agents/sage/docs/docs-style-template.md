---
name: docs-style-template
type: convention
status: approved
domain: docs
applies_to: "docs/**/*.html"
source: human
---

# Sage Docs — shared style + diagram assets

**How to use:** Sage docs no longer inline CSS/JS. The style and the zoom/pan
behavior live in two shared files **next to this template**:

- [`sage-docs.css`](sage-docs.css) — the full dark-theme stylesheet
- [`sage-docs.js`](sage-docs.js) — auto-wiring zoom/pan for every diagram

A generated `docs/<slug>.html` just **references** them (relative path from
`docs/` up to `agents/sage/docs/`):

```html
<head>
  …
  <link rel="stylesheet" href="../agents/sage/docs/sage-docs.css" />
</head>
<body>
  …
  <script src="../agents/sage/docs/sage-docs.js"></script>
</body>
```

This keeps every doc tiny (no 400-line `<style>` / 100-line `<script>` repeated
per file) and means a fix to the theme or zoom logic updates every doc at once.
**Do not paste the CSS/JS inline** — edit the shared files instead. This template
carries **no copyable CSS/JS**: the actual rules live in `sage-docs.css`, the
actual behavior in `sage-docs.js`. What's below is only reference (color
semantics) + the HTML structure scaffold to copy.

> Trade-off: a generated doc is no longer a single standalone file — it needs
> `agents/sage/docs/sage-docs.css|js` to sit in the same repo (they always do,
> since `agents/sage/` is the knowledge store shipped with the repo). To hand
> someone one truly standalone file, inline both manually as a one-off.

**What the stylesheet gives you:**

- Dark theme matching `sage.qorstack.com` (same tokens + gradients)
- Inter + JetBrains Mono fonts (Google Fonts via `@import`)
- Components: header, badges, TL;DR card, comp-meta grid, doc-section panels,
  narrative `doc-article`, diagram zoom/pan, quick-ref, tables, code, callouts,
  steps, conditions, footer — plus responsive (≤640 px) and print styles

**Diagram approach:**

- Inline `<svg>` with all drawing inside a `<g id="svg-content">` wrapper.
- `sage-docs.js` auto-discovers **every** `.svg-diagram` on the page and wires
  each one independently — no hardcoded IDs, no per-diagram script duplication.
- Controls are plain buttons with `data-zoom="in|out|fit"` (no inline `onclick`).
- Content size is auto-measured via `getBBox()` — you do **not** set SVG_W/SVG_H.
  Override only if needed with `data-w` / `data-h` on the `.svg-diagram` element.
- Never use CSS `transform` on a wrapper div (blurs at zoom) — the JS applies the
  transform to the `<g>` so it stays vector-sharp.

**Clean edges (avoid the "weird lines" look):**

- Connect from a node's **edge midpoint**, not its corner — e.g. parent bottom
  `(cx, y+h)` → child top `(cx, y)`. Compute `cx` as the node's true center.
- Prefer **orthogonal routing** (vertical then horizontal, right angles) over
  long diagonals. A shared bus line + short drops reads far cleaner than many
  crossing diagonals fanning from one point.
- Lay nodes on a **consistent grid** — equal column widths, aligned rows — so
  edges stay short and parallel. Misaligned nodes are what make lines look off.
- Keep the whole drawing's bounding box tight; the shared JS auto-centers it via
  `getBBox()`, so don't add huge empty margins or stray off-canvas elements
  (one stray element inflates the box and pushes everything off-center).

---

## Color semantics (cheat-sheet — values live in `sage-docs.css`)

Use this to pick which color a node/badge type should use when drawing an SVG.
These are **not** rules to copy — they're already defined as `:root` variables
in [`sage-docs.css`](sage-docs.css).

| Token            | Value                    | Use                           |
| ---------------- | ------------------------ | ----------------------------- |
| `--bg`           | `#050505`                | page background               |
| `--ink`          | `#f7f4ed`                | headings, high-emphasis text  |
| `--text`         | `#d7d0c2`                | body text                     |
| `--muted`        | `#8f897d`                | labels, captions              |
| `--line`         | `rgba(247,244,237,0.14)` | borders                       |
| `--panel-strong` | `#171714`                | section backgrounds           |
| `--mint`         | `#68d99b`                | architecture, success, arrows |
| `--cyan`         | `#71d7ff`                | API-flow, AI Agent node       |
| `--amber`        | `#f0c45c`                | user-journey, warnings        |
| `--violet`       | `#a98cff`                | backend-logic, docs output    |
| `--red`          | `#ff5a49`                | runbook, danger               |

The full rule set lives in [`sage-docs.css`](sage-docs.css) — edit there, not here.

---

## HTML scaffold for a zoomable diagram section

Buttons use `data-zoom`; the shared JS finds them. No `id` juggling needed — but
keeping `id="svg-content"` on the `<g>` is recommended (the JS prefers it).

```html
<section class="diagram-section">
  <h2>Overview</h2>
  <div class="diagram-label">
    {label · e.g. "click a node to jump to its section"}
  </div>
  <div class="diagram-container">
    <div class="svg-diagram">
      <div class="diagram-controls">
        <button data-zoom="in" title="Zoom in">+</button>
        <div class="sep"></div>
        <button data-zoom="out" title="Zoom out">−</button>
        <div class="sep"></div>
        <button data-zoom="fit" title="Reset" style="font-size:11px">
          fit
        </button>
        <div class="sep"></div>
        <span class="zoom-level">100%</span>
      </div>
      <svg
        width="100%"
        height="100%"
        xmlns="http://www.w3.org/2000/svg"
        style="font-family:'Inter',system-ui,sans-serif; display:block;"
      >
        <defs>
          <marker
            id="ar-mint"
            viewBox="0 0 10 8"
            refX="9"
            refY="4"
            markerWidth="6"
            markerHeight="5"
            orient="auto"
          >
            <polygon points="0,0 10,4 0,8" fill="#68d99b" opacity="0.8" />
          </marker>
          <marker
            id="ar-amber"
            viewBox="0 0 10 8"
            refX="9"
            refY="4"
            markerWidth="6"
            markerHeight="5"
            orient="auto"
          >
            <polygon points="0,0 10,4 0,8" fill="#f0c45c" opacity="0.7" />
          </marker>
          <marker
            id="ar-violet"
            viewBox="0 0 10 8"
            refX="9"
            refY="4"
            markerWidth="6"
            markerHeight="5"
            orient="auto"
          >
            <polygon points="0,0 10,4 0,8" fill="#a98cff" opacity="0.7" />
          </marker>
          <marker
            id="ar-cyan"
            viewBox="0 0 10 8"
            refX="9"
            refY="4"
            markerWidth="6"
            markerHeight="5"
            orient="auto"
          >
            <polygon points="0,0 10,4 0,8" fill="#71d7ff" opacity="0.8" />
          </marker>
        </defs>
        <!-- All drawing inside this <g> — the JS transforms it (no CSS scale = no blur) -->
        <g id="svg-content">
          <!-- nodes, lines, text. Wrap a node in <a href="#slug"> for click-to-jump. -->
        </g>
      </svg>
      <div class="diagram-hint">
        scroll to zoom · drag to pan · click node to jump
      </div>
    </div>
  </div>
  <p class="diagram-caption">{one-line caption}</p>
</section>
```

**Multiple diagrams per page:** just repeat the `.svg-diagram` block (overview +
one mini per endpoint). The shared JS wires each automatically — no extra
script, no slug-suffixed IDs. Mini diagrams add class `svg-diagram--mini`:
`<div class="svg-diagram svg-diagram--mini">`.
