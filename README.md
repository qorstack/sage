<p align="center"><img src="assets/logo-full.png" alt="Sage" width="640"></p>

<h1 align="center">Sage</h1>

<p align="center"><b>Make your AI code like your most senior dev.</b></p>

## The Sage

Every team has a senior who has seen it all — the one who, before touching
anything, quietly asks: _Is this even needed? Will it last? Is it safe? Did we
already agree on this?_ That balance of purpose and care has a name in Japan:
**生き甲斐 — ikigai**, your reason for doing.

Sage gives that senior's ikigai to **every AI agent you use**. Before it writes
a line, the agent becomes the right kind of senior for the task, weighs those
four questions against your team's rules, and _then_ codes — or stops and asks.

|     | the question      |                                                           |
| --- | ----------------- | --------------------------------------------------------- |
| 🎯  | **Is it needed?** | …or does something already cover it?                      |
| ⏳  | **Will it last?** | worth maintaining, in the shape the code already follows? |
| 🛡️  | **Is it safe?**   | what's the blast radius — money, auth, data?              |
| 🤝  | **Did we agree?** | does it respect the rules in `agents/sage/`?              |

No install, no server, no Python. Sage is a cognition protocol in a single
**[`AGENTS.md`](https://github.com/qorstack/sage/blob/main/AGENTS.md)** —
Markdown you read, edit, and `git push`. Any agent that reads `AGENTS.md`
(Claude Code, Cursor, Codex, Copilot…) follows it.

## Install — one file, any machine

### Let your AI set it up

Paste this into any AI coding agent (Claude Code, Cursor, Copilot, Windsurf…):

```text
Set up or update Sage in this repo.

(This prompt works for both first install and updating an existing Sage setup —
run it any time to get the latest files.)

1. Fetch https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md
   and save it as AGENTS.md at the repo root (overwrite if it already exists).
2. Detect which AI tools this repo uses by checking for .claude/, .cursor/,
   .windsurf/, .clinerules/, .github/instructions/, or GEMINI.md.
   For each one found, fetch the matching adapter from
   https://raw.githubusercontent.com/qorstack/sage/main/integrations/<tool-path>
   and save it (overwrite if it already exists). If none are found, ask me which
   tool I use.
3. Fetch https://raw.githubusercontent.com/qorstack/sage/main/agents/sage/index.md
   and save it as agents/sage/index.md (overwrite if it already exists).
4. Reply in **markdown** with two sections:

## Files installed / updated

List every file that was created or overwritten, with its full path relative to
the repo root, e.g.:

| File | Status |
|---|---|
| `AGENTS.md` | updated |
| `.claude/commands/sage.md` | updated |
| `agents/sage/index.md` | created |

## What to do next

List the four commands now available, one per line, with a one-sentence
description of each and **when** to run it:

- `/sage-learning` — **run first:** scans this codebase and writes team
  knowledge to `agents/sage/`
- `/sage-search-skill` — **run second:** researches best practices for this
  stack and adds them as skills
- `/sage` — **runs before every change:** full cognition pipeline — reads team
  knowledge, assesses risk, captures what it learned after
- `/sage-docs` — **on demand:** turns any document into a styled, self-contained
  HTML file with an interactive SVG diagram in `docs/`

Then ask: "Would you like me to run /sage-learning now to capture this
codebase's patterns?"
```

Or install manually:

### 1. Copy the protocol

Run this in your repo (works on Windows, macOS, and Linux):

```bash
curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md -o AGENTS.md
```

No terminal? Download
[`AGENTS.md`](https://github.com/qorstack/sage/blob/main/AGENTS.md)
and drop it in your repo root.

### 2. Wire up your agent

**Claude Code, Codex, OpenCode, Antigravity** read `AGENTS.md` natively — nothing else needed.

For **Cursor, Windsurf, Cline, Copilot, Gemini**, copy the thin adapter for your tool:

| Tool           | Command                            |
| -------------- | ---------------------------------- |
| Claude Code    | `cp -r integrations/.claude .`     |
| Cursor         | `cp -r integrations/.cursor .`     |
| Windsurf       | `cp -r integrations/.windsurf .`   |
| Cline          | `cp -r integrations/.clinerules .` |
| GitHub Copilot | `cp -r integrations/.github .`     |
| Gemini CLI     | `cp integrations/GEMINI.md .`      |

Each adapter is one line: "read and follow `AGENTS.md`." Edit the protocol in
one place and every agent stays in step.

### 3. Optionally seed starter knowledge

```bash
git clone --depth 1 https://github.com/qorstack/sage t && cp -r t/agents . && rm -rf t
```

Commit everything. That's the whole setup.

## Getting started — run in this order

After installing, run these commands in sequence. Each builds on the last.

| # | Command | When | What it does |
| --- | --- | --- | --- |
| 1 | `/sage-learning` | **Once after install** | Scans your codebase, writes rules + decisions to `agents/sage/`. Gives Sage a baseline of your real patterns before it touches anything. |
| 2 | `/sage-search-skill` | **Once, then after stack changes** | Searches for current best practices for your stack and writes them as skills. Run again when you adopt a new framework or library. |
| 3 | `/sage` | **Every code change (automatic via AGENTS.md)** | Runs the full pipeline: pick role → read knowledge → assess risk → code → capture → summarize. Happens automatically — you don't call it manually, AGENTS.md enforces it. |
| 4 | `/sage-docs` | **On demand** | Turns any spec, README, or meeting note into a styled, self-contained HTML file with an interactive SVG diagram (zoom/pan). Use when a teammate needs to read — not when an AI needs to follow. |

> **Skip step 1?** Sage still works — it just starts with no team context.
> Run `/sage-learning` later whenever you want to seed knowledge from real code.

---

## Commands

Four commands cover the full lifecycle:

**`/sage`** — run the full cognition pipeline before any code change

Before writing, the agent establishes its role, reads team knowledge, and states
intent + risk. After writing, it captures what it learned and closes with a
summary. Every field is mandatory — a response without the summary block is
considered incomplete.

```text
/sage fix infinite API loop on the material create page

Role    : debugger — root-causing repeated GET /usage-plans calls
Intent  : stop useCallback from recreating on every render
Touches : src/views/apps/boq/request/BoqUsagePlanSection.tsx
Risk    : LOW — dependency array fix, no logic change
Decision: proceed

... [fix applied] ...

── Sage ──────────────────────────────────────────
Role      : debugger — fix infinite API loop in BoqUsagePlanSection
Domain    : frontend  |  Risk: LOW

Root cause: useLoadingScreen() returns a new object literal { start, stop } on
            every render because it does not wrap its return value in useMemo.
            Including this in useCallback's dep array makes the hook treat it as
            a new dependency on every render.

Mechanism : Every render → new loadingScreen object → useCallback recreated →
            useEffect fires → API called → setState → re-render → repeat.
            This caused hundreds of GET /usage-plans calls per page load.

Fix       : Removed loadingScreen and handleError from the dep array, keeping
            only [materialId]. Both are used for side-effects only and their
            instability cannot cause stale-closure bugs.

Validated : Network tab after fix shows one GET /usage-plans on load, one more
            when materialId changes. The repeat loop is gone.

Slipped   : useLoadingScreen's API looks stable (named methods) but returns a
            plain object literal without useMemo — non-obvious without reading
            the hook source.

Knowledge : [new] agents/sage/frontend/decisions/usecallback-unstable-deps.md
                  → "Never put hook-returned objects in useCallback deps"
──────────────────────────────────────────────────
```

**`/sage-learning`** — scan this codebase once and write team knowledge

```text
/sage-learning

── Sage Learning ─────────────────────────────────
Stack     : TypeScript, Next.js 15, React 19, MUI, Valibot
Domains   : frontend, api, auth, billing
Written   :
  [new]     agents/sage/frontend/rules.md — naming, layout, and hook conventions
  [new]     agents/sage/frontend/decisions/usecallback-unstable-deps.md
  [new]     agents/sage/frontend/decisions/react-hook-deps-stability.md
  [updated] agents/sage/roles/role-frontend.md — added hooks/state section
  [skipped] loading-and-error-pattern.md — already up to date
Next      : flip status: approved on entries you want enforced
──────────────────────────────────────────────────
```

**`/sage-search-skill`** — research current best practices for this stack and write them as skills

```text
/sage-search-skill

Stack detected: TypeScript + React + Tailwind
Researched: component patterns, accessibility, performance, 2025 trends
Written: agents/sage/frontend/skills/component-composition.md
Written: agents/sage/frontend/skills/avoid-premature-abstraction.md
Written: agents/sage/frontend/skills/server-component-boundaries.md
6 skills added — review and approve
```

**`/sage-docs`** — turn any document into a styled, self-contained HTML file with an interactive SVG diagram

Give it any source material — a spec, README, API contract, PRD, meeting note.
Sage classifies the doc type, decides if a diagram fits, generates an inline SVG
diagram with zoom/pan (scroll to zoom, drag to pan) with full technical detail
(exact endpoints, conditions, storage ops), and writes a single self-contained
`docs/<slug>.html` with CSS inlined from the shared template.

```text
/sage-docs  [paste or describe the document]

Doc type   · api-flow
Diagram    · inline SVG — POST /api/v1/orders, GET /api/v1/products
Output     · docs/checkout-flow.html
CSS        · inlined from agents/sage/docs/docs-style-template.md

Sections written
- Overview Diagram — interactive SVG: frontend → API → DB with exact endpoints + error cases
- Quick Reference — endpoint summary table (method, path, auth, purpose)
- Endpoint Detail — request body schema, 201 response, 4xx error table
- Notes — idempotency, retry behavior
```

## Your rules, as Markdown

Knowledge lives in `agents/sage/<domain>/` — plain Markdown with a little YAML:

```markdown
---
title: Use idempotency keys
domain: billing
status: approved
enforcement: block # block | warn | advise
---

All payment calls MUST pass an idempotency key. No exceptions.
```

Edit a rule, commit, done — the agent follows your version. When you tell it a
new rule in chat, it writes one as `status: proposed`; you approve by flipping it
to `approved`. It even keeps a library of senior personas in `agents/sage/roles/`.

Run **`/sage-learning`** once to seed `agents/sage/` straight from your existing
code — Sage studies the team's real patterns and writes them up so future code
matches. Then run **`/sage-docs`** any time you need a document a human will
open in a browser, not an AI.

## Works with every agent

`AGENTS.md` is read natively by **Claude Code, Codex, OpenCode, Antigravity**.
For **Cursor, Windsurf, Cline, Copilot, Gemini**, drop in a one-line adapter from
[`integrations/`](integrations/) — each just points the tool at `AGENTS.md`.

---

MIT — see [LICENSE](LICENSE). · [sage.qorstack.com](https://sage.qorstack.com)
