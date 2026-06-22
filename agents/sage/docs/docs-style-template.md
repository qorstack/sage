---
name: docs-style-template
type: convention
status: approved
domain: docs
applies_to: "docs/**/*.html"
source: human
---

# Sage Docs — CSS Template

**How to use:** When generating a `docs/*.html` file, read this file, extract
the CSS from the fenced code block below, and paste it verbatim inside a
`<style>` tag in the HTML `<head>`. Do not link an external stylesheet — every
doc must be a self-contained single file.

**What it gives you:**
- Dark theme matching `sage.qorstack.com` exactly (same CSS variables, same gradients)
- Inter + JetBrains Mono fonts (Google Fonts via `@import`)
- Components: header, badges, sections, diagram zoom/pan, quick-ref grid, tables,
  code blocks, callouts, steps, conditions, endpoints, footer
- Responsive (≤640 px) and print styles
- Zoomable inline SVG diagram infrastructure (`.svg-diagram`, `.diagram-controls`)

**Diagram approach:** Use inline `<svg>` with a `<g id="svg-content">` wrapper.
Apply pan/zoom via `group.setAttribute('transform', …)` in JavaScript — never
CSS `transform` on a wrapper div (causes blurring at zoom). See the JS block
in `docs/sage-architecture.html` for the canonical implementation.

---

## Design tokens

| Token | Value | Use |
|---|---|---|
| `--bg` | `#050505` | page background |
| `--ink` | `#f7f4ed` | headings, high-emphasis text |
| `--text` | `#d7d0c2` | body text |
| `--muted` | `#8f897d` | labels, captions |
| `--line` | `rgba(247,244,237,0.14)` | borders |
| `--panel-strong` | `#171714` | section backgrounds |
| `--mint` | `#68d99b` | architecture, success, arrows |
| `--cyan` | `#71d7ff` | API-flow, AI Agent node |
| `--amber` | `#f0c45c` | user-journey, warnings |
| `--violet` | `#a98cff` | backend-logic, docs output |
| `--red` | `#ff5a49` | runbook, danger |

---

## CSS

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
  --bg:           #050505;
  --ink:          #f7f4ed;
  --text:         #d7d0c2;
  --muted:        #8f897d;
  --line:         rgba(247, 244, 237, 0.14);
  --panel:        rgba(20, 20, 18, 0.82);
  --panel-strong: #171714;
  --red:          #ff5a49;
  --amber:        #f0c45c;
  --mint:         #68d99b;
  --cyan:         #71d7ff;
  --violet:       #a98cff;
  --font-body: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Consolas, monospace;
  --max-width:  900px;
  --radius:     8px;
  --radius-sm:  4px;
  --radius-lg:  12px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; width: 100%; overflow-x: clip; }
img, svg { display: block; max-width: 100%; }
a { color: var(--mint); text-decoration: none; }
a:hover { color: var(--ink); text-decoration: underline; }

body {
  font-family: var(--font-body);
  font-weight: 400;
  line-height: 1.65;
  color: var(--text);
  background:
    radial-gradient(circle at 16% 12%, rgba(255, 90, 73, 0.12), transparent 28rem),
    radial-gradient(circle at 86% 20%, rgba(113, 215, 255, 0.08), transparent 30rem),
    linear-gradient(180deg, #080807 0%, #050505 42%, #0b0a08 100%);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  background-image:
    linear-gradient(rgba(247, 244, 237, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(247, 244, 237, 0.03) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: linear-gradient(180deg, black 0%, transparent 80%);
}

h1, h2, h3, h4, h5 { color: var(--ink); font-weight: 700; line-height: 1.25; }
h1 { font-size: 1.9rem;  margin-bottom: 12px; }
h2 { font-size: 1.15rem; margin-bottom: 12px; margin-top: 32px; }
h3 { font-size: 0.95rem; margin-bottom: 8px;  margin-top: 24px; font-weight: 600; }
h4 { font-size: 0.875rem; margin-bottom: 6px; margin-top: 18px; font-weight: 500; color: var(--text); }

p  { margin-bottom: 14px; }
ul, ol { padding-left: 22px; margin-bottom: 14px; }
li { margin-bottom: 4px; }
li > ul, li > ol { margin-top: 4px; margin-bottom: 0; }
hr { border: none; border-top: 1px solid var(--line); margin: 32px 0; }

/* ── Layout ── */
.doc-wrapper { max-width: var(--max-width); margin: 0 auto; padding: 48px 24px 80px; }

/* ── Header ── */
.doc-header {
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 32px;
  margin-bottom: 24px;
}
.breadcrumb {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.breadcrumb a { color: var(--muted); }
.breadcrumb a:hover { color: var(--ink); text-decoration: none; }
.breadcrumb-sep { color: rgba(247, 244, 237, 0.25); }
.doc-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
.doc-header h1 { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 10px; }
.doc-subtitle { font-size: 0.975rem; color: var(--text); font-weight: 400; margin: 0; line-height: 1.6; max-width: 70ch; }
.doc-date { font-family: var(--font-mono); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin-top: 16px; }

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}
.badge-api-flow      { background: rgba(113, 215, 255, 0.14); color: var(--cyan);   border: 1px solid rgba(113, 215, 255, 0.25); }
.badge-backend-logic { background: rgba(169, 140, 255, 0.14); color: var(--violet); border: 1px solid rgba(169, 140, 255, 0.25); }
.badge-architecture  { background: rgba(104, 217, 155, 0.14); color: var(--mint);   border: 1px solid rgba(104, 217, 155, 0.25); }
.badge-user-journey  { background: rgba(240, 196, 92, 0.14);  color: var(--amber);  border: 1px solid rgba(240, 196, 92, 0.25); }
.badge-runbook       { background: rgba(255, 90, 73, 0.14);   color: var(--red);    border: 1px solid rgba(255, 90, 73, 0.25); }
.badge-data-schema   { background: rgba(104, 217, 155, 0.14); color: var(--mint);   border: 1px solid rgba(104, 217, 155, 0.25); }
.badge-general       { background: rgba(247, 244, 237, 0.08); color: var(--muted);  border: 1px solid var(--line); }
.badge-domain        { background: rgba(247, 244, 237, 0.06); color: var(--muted);  border: 1px solid var(--line); }
.badge-method { font-family: var(--font-mono); font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: var(--radius-sm); text-transform: uppercase; letter-spacing: 0.06em; }
.badge-get    { background: rgba(104, 217, 155, 0.15); color: var(--mint); }
.badge-post   { background: rgba(113, 215, 255, 0.15); color: var(--cyan); }
.badge-put    { background: rgba(240, 196, 92, 0.15);  color: var(--amber); }
.badge-patch  { background: rgba(240, 196, 92, 0.15);  color: var(--amber); }
.badge-delete { background: rgba(255, 90, 73, 0.15);   color: var(--red); }

/* ── Section panel ── */
.doc-section {
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 0;
  margin-bottom: 16px;
  overflow: hidden;
}
.doc-section > h2:first-child {
  margin-top: 0;
  padding: 14px 24px;
  background: rgba(247, 244, 237, 0.04);
  border-bottom: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-section > *:not(h2:first-child) { padding-left: 24px; padding-right: 24px; }
.doc-section > *:last-child { padding-bottom: 24px; }
.doc-section > h2:first-child + * { margin-top: 20px; }
.doc-section > h3 { margin-top: 20px; }

/* ── Diagram section ── */
.diagram-section {
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-top: 2px solid var(--mint);
  border-radius: var(--radius-lg);
  padding: 0;
  margin-bottom: 16px;
  overflow: hidden;
}
.diagram-section > h2 {
  margin-top: 0;
  padding: 14px 24px;
  background: rgba(104, 217, 155, 0.06);
  border-bottom: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--mint);
  display: flex;
  align-items: center;
  gap: 8px;
}
.diagram-label {
  padding: 0 24px;
  margin-top: 16px;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}
.diagram-container {
  margin: 12px 24px 0;
  background: rgba(5, 5, 5, 0.6);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px;
  overflow: hidden;
}
.diagram-container svg { max-width: 100%; margin: 0 auto; }
.diagram-caption {
  padding: 10px 24px 20px;
  font-size: 0.78rem;
  color: var(--muted);
  font-style: italic;
  text-align: center;
}

/* ── Zoomable inline SVG diagram ── */
.svg-diagram {
  background: rgba(5, 5, 5, 0.5);
  border-radius: var(--radius);
  position: relative;
  overflow: hidden;
  height: 480px;
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
}
.svg-diagram.is-dragging { cursor: grabbing; }
.diagram-controls {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 20;
  display: flex;
  gap: 2px;
  align-items: center;
  background: rgba(20, 20, 18, 0.9);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 4px 6px;
  backdrop-filter: blur(8px);
}
.diagram-controls button {
  background: none;
  border: none;
  color: var(--text);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  transition: background 0.12s;
}
.diagram-controls button:hover { background: var(--line); color: var(--ink); }
.diagram-controls .sep { width: 1px; height: 16px; background: var(--line); margin: 0 2px; }
.zoom-level { color: var(--muted); font-size: 10px; font-family: var(--font-mono); min-width: 34px; text-align: center; padding: 0 4px; }
.diagram-hint {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: rgba(143, 137, 125, 0.5);
  font-family: var(--font-mono);
  pointer-events: none;
  white-space: nowrap;
}

/* ── Quick reference ── */
.quick-ref {
  background: rgba(247, 244, 237, 0.03);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  margin-bottom: 16px;
}
.quick-ref > h2 { margin-top: 0; font-family: var(--font-mono); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 16px; }
.quick-ref-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; }
.quick-ref-item { background: var(--panel-strong); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px 14px; }
.quick-ref-label { font-family: var(--font-mono); font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 4px; }
.quick-ref-value { font-size: 0.875rem; color: var(--ink); font-weight: 500; }

/* ── Tables ── */
.table-wrap { overflow-x: auto; margin-bottom: 16px; border-radius: var(--radius); border: 1px solid var(--line); }
table { width: 100%; border-collapse: collapse; font-size: 0.855rem; }
thead th { background: rgba(247, 244, 237, 0.05); color: var(--muted); font-family: var(--font-mono); font-weight: 700; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--line); white-space: nowrap; }
tbody tr { border-bottom: 1px solid rgba(247, 244, 237, 0.06); }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: rgba(247, 244, 237, 0.03); }
tbody td { padding: 10px 14px; vertical-align: top; line-height: 1.5; color: var(--text); }
tbody td:first-child { color: var(--ink); font-weight: 500; }

/* ── Code ── */
code { font-family: var(--font-mono); font-size: 0.82em; background: rgba(247, 244, 237, 0.08); color: var(--cyan); padding: 2px 6px; border-radius: var(--radius-sm); border: 1px solid rgba(247, 244, 237, 0.1); }
pre { background: #060605; border: 1px solid var(--line); border-radius: var(--radius); padding: 18px; overflow-x: auto; margin-bottom: 14px; font-size: 0.82rem; line-height: 1.65; color: var(--ink); }
pre code { background: none; border: none; padding: 0; color: inherit; font-size: inherit; }

/* ── Callout boxes ── */
.callout { display: flex; gap: 12px; padding: 14px 16px; border-radius: var(--radius); margin-bottom: 14px; font-size: 0.875rem; border-left: 2px solid; }
.callout-icon { flex-shrink: 0; font-size: 0.95rem; line-height: 1.65; }
.callout-info    { background: rgba(113, 215, 255, 0.08); border-color: var(--cyan);   color: var(--text); }
.callout-warning { background: rgba(240, 196, 92, 0.08);  border-color: var(--amber);  color: var(--text); }
.callout-danger  { background: rgba(255, 90, 73, 0.08);   border-color: var(--red);    color: var(--text); }
.callout-success { background: rgba(104, 217, 155, 0.08); border-color: var(--mint);   color: var(--text); }
.callout-note    { background: rgba(247, 244, 237, 0.05); border-color: var(--muted);  color: var(--text); }

/* ── Conditions ── */
.conditions-list { list-style: none; padding: 0; }
.condition-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--line); }
.condition-item:last-child { border-bottom: none; }
.condition-when { flex-shrink: 0; background: rgba(247, 244, 237, 0.05); color: var(--muted); border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 1px 8px; font-family: var(--font-mono); font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }
.condition-then { font-size: 0.875rem; color: var(--text); }

/* ── Endpoint block ── */
.endpoint-block { background: #060605; border: 1px solid var(--line); border-radius: var(--radius); padding: 12px 16px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.endpoint-path { font-family: var(--font-mono); font-size: 0.875rem; color: var(--ink); font-weight: 500; }
.endpoint-desc { font-size: 0.82rem; color: var(--muted); margin-left: auto; }

/* ── Steps ── */
.steps-list { list-style: none; padding: 0; }
.step-item { display: flex; gap: 14px; margin-bottom: 20px; }
.step-number { flex-shrink: 0; width: 26px; height: 26px; background: var(--mint); color: #050505; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 0.72rem; font-weight: 700; margin-top: 2px; }
.step-content { flex: 1; }
.step-title { font-weight: 600; color: var(--ink); margin-bottom: 3px; }
.step-detail { font-size: 0.875rem; color: var(--text); }

/* ── Footer ── */
.doc-footer { border-top: 1px solid var(--line); padding-top: 24px; margin-top: 48px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; font-family: var(--font-mono); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }
.doc-footer a { color: var(--muted); }
.doc-footer a:hover { color: var(--ink); text-decoration: none; }
.sage-brand { display: flex; align-items: center; gap: 8px; font-weight: 700; color: var(--ink); }

/* ── Responsive ── */
@media (max-width: 640px) {
  .doc-wrapper { padding: 24px 16px 60px; }
  .doc-header  { padding: 20px; }
  .doc-header h1 { font-size: 1.45rem; }
  .quick-ref-grid { grid-template-columns: 1fr 1fr; }
  .diagram-container { margin: 12px 16px 0; padding: 12px; }
  .doc-footer { flex-direction: column; text-align: center; }
}

/* ── Print ── */
@media print {
  body { background: #fff; color: #1a1a1a; }
  body::before { display: none; }
  .doc-header, .doc-section, .diagram-section, .quick-ref { border: 1px solid #ccc; background: #fff; }
  h1, h2, h3, h4 { color: #111; }
  code { background: #f5f5f5; color: #333; border-color: #ddd; }
  .badge { border: 1px solid #ccc; color: #333; background: #eee; }
}
```

---

## Zoom/Pan JavaScript (for zoomable SVG diagrams)

Include this `<script>` block at the end of `<body>` whenever the doc has a
zoomable diagram. Replace `SVG_W` / `SVG_H` with the actual SVG content
dimensions (i.e. the numbers in `viewBox`).

```js
(function () {
  var container = document.getElementById('svg-zoom-container');
  var group     = document.getElementById('svg-content');
  var label     = document.getElementById('zoom-label');
  var SVG_W = 780, SVG_H = 518; /* replace with actual diagram dimensions */
  var scale = 1, tx = 0, ty = 0;
  var dragging = false, startX, startY, startTx, startTy;

  function fitScale() {
    var cw = container.clientWidth  - 40;
    var ch = container.clientHeight - 40;
    return Math.min(cw / SVG_W, ch / SVG_H, 1.6);
  }
  function apply() {
    group.setAttribute('transform',
      'translate(' + tx + ',' + ty + ') scale(' + scale + ')');
    label.textContent = Math.round(scale * 100) + '%';
  }
  function initFit() {
    scale = fitScale();
    tx = (container.clientWidth  - SVG_W * scale) / 2;
    ty = (container.clientHeight - SVG_H * scale) / 2;
    apply();
  }

  globalThis.diagramZoomIn  = function () { scale = Math.min(scale * 1.3, 8); apply(); };
  globalThis.diagramZoomOut = function () { scale = Math.max(scale / 1.3, 0.1); apply(); };
  globalThis.diagramZoomFit = function () { initFit(); };

  container.addEventListener('wheel', function (e) {
    e.preventDefault();
    var rect = container.getBoundingClientRect();
    var mx = e.clientX - rect.left, my = e.clientY - rect.top;
    var prev = scale, delta = e.deltaY > 0 ? 0.88 : 1.14;
    scale = Math.min(Math.max(scale * delta, 0.1), 8);
    tx = mx - (mx - tx) * (scale / prev);
    ty = my - (my - ty) * (scale / prev);
    apply();
  }, { passive: false });

  container.addEventListener('mousedown', function (e) {
    dragging = true; startX = e.clientX; startY = e.clientY;
    startTx = tx; startTy = ty;
    container.classList.add('is-dragging');
  });
  globalThis.addEventListener('mousemove', function (e) {
    if (!dragging) return;
    tx = startTx + (e.clientX - startX);
    ty = startTy + (e.clientY - startY);
    apply();
  });
  globalThis.addEventListener('mouseup', function () {
    dragging = false;
    container.classList.remove('is-dragging');
  });

  var lastDist = null;
  container.addEventListener('touchstart', function (e) {
    if (e.touches.length === 2) {
      var t1 = e.touches[0], t2 = e.touches[1];
      lastDist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
    } else if (e.touches.length === 1) {
      dragging = true;
      startX = e.touches[0].clientX; startY = e.touches[0].clientY;
      startTx = tx; startTy = ty;
    }
  }, { passive: true });
  container.addEventListener('touchmove', function (e) {
    if (e.touches.length === 2) {
      e.preventDefault();
      var t1 = e.touches[0], t2 = e.touches[1];
      var dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      var rect = container.getBoundingClientRect();
      var mx = (t1.clientX + t2.clientX) / 2 - rect.left;
      var my = (t1.clientY + t2.clientY) / 2 - rect.top;
      if (lastDist) {
        var ratio = dist / lastDist, prev = scale;
        scale = Math.min(Math.max(scale * ratio, 0.1), 8);
        tx = mx - (mx - tx) * (scale / prev);
        ty = my - (my - ty) * (scale / prev);
        apply();
      }
      lastDist = dist;
    } else if (e.touches.length === 1 && dragging) {
      tx = startTx + (e.touches[0].clientX - startX);
      ty = startTy + (e.touches[0].clientY - startY);
      apply();
    }
  }, { passive: false });
  container.addEventListener('touchend', function () {
    dragging = false; lastDist = null;
  });

  initFit();
})();
```

## HTML scaffold for zoomable diagram section

```html
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
        <!-- arrow markers in <defs> — use #ar-mint, #ar-amber, #ar-violet, #ar-cyan -->
        <defs>
          <marker id="ar-mint" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto">
            <polygon points="0,0 10,4 0,8" fill="#68d99b" opacity="0.8"/>
          </marker>
          <marker id="ar-amber" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto">
            <polygon points="0,0 10,4 0,8" fill="#f0c45c" opacity="0.7"/>
          </marker>
          <marker id="ar-violet" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto">
            <polygon points="0,0 10,4 0,8" fill="#a98cff" opacity="0.7"/>
          </marker>
          <marker id="ar-cyan" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto">
            <polygon points="0,0 10,4 0,8" fill="#71d7ff" opacity="0.8"/>
          </marker>
        </defs>
        <!-- All SVG drawing inside this <g> — JS transforms it (no CSS scale = no blur) -->
        <g id="svg-content">
          <!-- your nodes, lines, text here -->
        </g>
      </svg>
      <div class="diagram-hint">scroll to zoom · drag to pan</div>
    </div>
  </div>
  <p class="diagram-caption">{one-line caption}</p>
</section>
```
