# Landing dark hero — frontend flow

> Redesign the static `landing/index.html` first view around Sage's real product
> promise: a visible judgment step before code. The page remains a dependency-free
> GitHub Pages artifact. Design verified against the source on 2026-09-21.

## Design decisions

Use a charcoal workspace palette rather than a neon developer theme. A muted
sage family marks attention, controls, and verified outcomes without competing
accent hues. Preserve
IBM Plex Sans and Mono because the existing editorial/trace pairing fits the
product and avoids a new font dependency.

## 1. Actors & systems

| System | Responsibility | Ownership |
| --- | --- | --- |
| Visitor | Understand Sage and choose install or source | User |
| Browser | Render the responsive page and run local tab/copy interactions | Client |
| `landing/index.html` | Own all HTML, CSS, and JavaScript | Repository |
| GitHub Pages | Serve the checked-in `landing/` directory | Deployment |

**Trust boundary:** The page is static. It must not collect user data, introduce
credentials, or claim runtime behavior Sage does not provide.

## 2. End-to-end overview

```text
[Visitor] opens the Sage landing page
   |
   v Browser renders dark navigation + hero (no API)
   |
[Hero] promise + decision trace explain cognition before code
   |-- Install Sage -> scroll to #install
   `-- Read the source -> open GitHub in a new tab
   |
   v Existing sections explain protocol, install, and usage
   |
[Install] OS tab selects a local command -> Copy writes it to clipboard
```

**Key:** The first viewport must explain both the outcome (better judgment) and
the mechanism (context, reuse, risk, evidence) without relying on later sections.

## 3. Step-by-step

### Step 1 — Render the first view

**System:** Browser / `landing/index.html`

When the document loads -> render a sticky dark navigation, left-aligned product
promise, two clear actions, and the existing decision trace -> the visitor can
understand the product before scrolling. When motion reduction is requested ->
disable the entrance sequence -> preserve the same information without motion.

### Step 2 — Choose the next action

**System:** Browser

When `Install Sage` is activated -> navigate to `#install` -> expose the existing
installer. When `Read the source` is activated -> open the repository with
`noopener` -> preserve the landing page session.

### Step 3 — Continue through the existing page

**System:** Browser / existing page sections

When the visitor scrolls -> reuse the existing problem, protocol, comparison,
install, usage, workspace, and closing content -> keep the redesign bounded to
theme and first-view hierarchy.

## 4. State and data handling

Only the existing installer tab selection and temporary copy-label state exist.
No persistent state, cookies, analytics, forms, or user data are added.

## 5. API spec

N/A. The landing page makes no application API calls. The existing external
links and font stylesheet remain unchanged.

## 6. Status lifecycle

N/A. Visual states are limited to focus, hover, selected OS tab, and the
short-lived `Copied` label.

## 7. Data model touchpoints

N/A. No storage or schema is involved.

## 8. Edge cases and error handling

| Case | Handling |
| --- | --- |
| Narrow viewport | Stack hero content, keep actions usable, simplify navigation |
| Very long command | Allow wrapping without overflowing its panel |
| Clipboard unavailable | Keep the existing safe no-op behavior |
| Reduced motion | Remove entrance animation and smooth scrolling |
| Keyboard navigation | Show high-contrast focus rings on every action |
| External font unavailable | Fall back to system sans and monospace fonts |

## 9. Security and concurrency

No auth, secrets, money, or concurrency exist. External links retain
`rel="noopener"`; the redesign adds no scripts, trackers, or remote data flows.

## 10. Build checklist

- [x] **LANDING-01 — Dark token system** (`landing/index.html`)
  - Depends on: none
  - Acceptance: when any section renders -> text, borders, focus, and status
    colors meet readable contrast -> the whole page is consistently dark.
- [x] **LANDING-02 — Hero hierarchy** (`landing/index.html`)
  - Depends on: LANDING-01
  - Acceptance: when the first viewport renders -> promise, actions, product
    mechanism, and decision trace are clear on desktop and mobile.
- [x] **LANDING-03 — Documentation and visual validation**
  - Depends on: LANDING-01, LANDING-02
  - Acceptance: when local validation runs -> HTML parses, links and controls
    remain present, and screenshots show no overflow at desktop or mobile widths.

## 11. Open questions

None. Product behavior and copy remain unchanged; palette and layout are
reversible implementation choices within the requested dark redesign.

## Out of scope

- Product copy beyond the hero's supporting labels
- New APIs, analytics, frameworks, or package dependencies
- Changing install commands or JavaScript behavior
- Redesigning the logo asset
