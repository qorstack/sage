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

No server, no build, no Python. Sage is a cognition protocol —
**[`AGENTS.md`](https://github.com/qorstack/sage/blob/main/AGENTS.md)** plus a
folder of Markdown commands and team knowledge you read, edit, and `git push`.
One command installs it; any agent that reads `AGENTS.md` (Claude Code, Cursor,
Codex, Copilot…) follows it.

## Install — one command

Run this in your repo. It **asks which AI tools to wire up** (multi-select:
Claude Code, Cursor, Windsurf, Cline, Copilot, Codex, Gemini), fetches the
protocol + commands, and drops the adapters you pick. Re-run any time to update.

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/qorstack/sage/main/install.ps1 | iex
```

**macOS / Linux:**

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh)"
```

It never overwrites your own knowledge under `agents/sage/<domain>/` — only
Sage's own system files (the protocol, the commands, the style-guide) and the
tool adapters. Then run `/sage-learning` to seed knowledge from your codebase.

<details>
<summary><b>Prefer to install by hand?</b></summary>

**1. Copy the protocol.** Download
[`AGENTS.md`](https://github.com/qorstack/sage/blob/main/AGENTS.md) into your repo
root, then copy `agents/sage/` from this repo (the canonical commands, the
style-guide, and starter knowledge). Or clone and copy:

```bash
git clone --depth 1 https://github.com/qorstack/sage t && cp t/AGENTS.md . && cp -r t/agents . && rm -rf t
```

**2. Wire up your agent.** **Claude Code, Codex, OpenCode, Antigravity** read
`AGENTS.md` natively. For the rest, copy the thin adapter for your tool:

| Tool           | Command                                 |
| -------------- | --------------------------------------- |
| Claude Code    | `cp -r integrations/.claude .`          |
| Cursor         | `cp -r integrations/.cursor .`          |
| Windsurf       | `cp -r integrations/.windsurf .`        |
| Cline          | `cp -r integrations/.clinerules .`      |
| GitHub Copilot | `cp -r integrations/.github .`          |
| Codex          | `cp -r integrations/.codex .`           |
| Gemini CLI     | `cp integrations/gemini.md ./GEMINI.md` |

Each adapter is thin — it points at `AGENTS.md` and the canonical commands under
`agents/sage/commands/`. Edit the protocol in one place and every agent stays in
step.

</details>

Commit everything. That's the whole setup.

## Getting started — run in this order

After installing, run these commands in sequence. Each builds on the last.

| #   | Command              | When                                            | What it does                                                                                                                                                                                                                                    |
| --- | -------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `/sage-learning`     | **Once after install**                          | Scans your codebase, writes rules + decisions to `agents/sage/`. Gives Sage a baseline of your real patterns before it touches anything.                                                                                                        |
| 2   | `/sage-search-skill` | **Once, then after stack changes**              | Searches for current best practices for your stack and writes them as skills. Run again when you adopt a new framework or library.                                                                                                              |
| 3   | `/sage`              | **Every code change (automatic via AGENTS.md)** | Runs the full pipeline: pick role → read knowledge → assess risk → code → capture → summarize. Happens automatically — you don't call it manually, AGENTS.md enforces it.                                                                       |
| 4   | `/sage-docs`         | **On demand**                                   | Turns any spec, README, or meeting note into a plain-Markdown flow doc (`docs/<slug>.md`) — end-to-end ASCII diagram, full step-by-step, complete API spec, open questions. Use when a teammate needs to read — not when an AI needs to follow. |

> **Skip step 1?** Sage still works — it just starts with no team context.
> Run `/sage-learning` later whenever you want to seed knowledge from real code.

**You mostly just use `/sage`.** Before each change it shows a short **checklist**
and — once you confirm — runs the right specialist command itself, so you don't
have to remember them:

| Checklist item    | Runs                    | For                                      |
| ----------------- | ----------------------- | ---------------------------------------- |
| `plan-flow`       | `/sage-flow`            | design the flow before coding            |
| `unit-test`       | `/sage-unit-test`       | write unit tests for what changed        |
| `n2n-test`        | `/sage-n2n-test`        | drive the flow end-to-end (browser/load) |
| `security-review` | `/sage-security-review` | check sensitive changes for holes        |
| `update-docs`     | `/sage-docs`            | refresh the human-facing docs            |

Sage auto-checks what fits the task and auto-unchecks what doesn't (with a
reason) — you confirm, it runs. Every command's full body lives once in
`agents/sage/commands/`; the per-tool files just point at it.

---

## Commands

The lifecycle commands you run directly:

**`/sage`** — run the full cognition pipeline before any code change

Before writing, the agent establishes its role, selects the appropriate model
and effort tier for the task (never exceeding the session ceiling), reads team
knowledge, and states intent + risk. After writing, it captures what it learned
and closes with a summary that includes the model + effort used. Every field is
mandatory — a response without the summary block is considered incomplete.

```text
/sage fix infinite API loop on the material create page

Role    : debugger — root-causing repeated GET /usage-plans calls
Model   : sonnet 4.6 @ effort:medium
Intent  : stop useCallback from recreating on every render
Touches : src/views/apps/boq/request/BoqUsagePlanSection.tsx
Risk    : LOW — dependency array fix, no logic change
Decision: proceed

... [fix applied] ...

── Sage ──────────────────────────────────────────
Role      : debugger — fix infinite API loop in BoqUsagePlanSection
Model     : sonnet 4.6 @ effort:medium
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

**`/sage-docs`** — turn any document into a plain-Markdown flow doc

Give it any source material — a spec, README, API contract, PRD, meeting note.
Sage classifies the doc type, builds an end-to-end ASCII flow, then writes
`docs/<slug>.md` with full technical detail (actors → step-by-step → complete API
spec → edge cases → security → open questions). Plain Markdown — no CSS/JS, no
browser; it reads on GitHub and diffs cleanly in a PR. Then it verifies the flow
as a skeptic and asks you about anything genuinely uncertain before finishing.

```text
/sage-docs  [paste or describe the document]

Language   · English
Doc type   · api-flow
Output     · docs/checkout-flow.md
Systems    · Website, Service, Payment-service
Sections   · Actors · Overview (ASCII) · Steps · API spec · Edge cases · Security · Open Questions
Coverage   · 7 steps · 8 endpoints · 6 errors — all covered
Open Q     · 2 (asked: SUB number timing · flat vs ranged fee)
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
matches. Then run **`/sage-docs`** any time you need a flow doc a human will read
on GitHub, not an AI.

## Works with every agent

`AGENTS.md` is read natively by **Claude Code, Codex, OpenCode, Antigravity**.
For **Cursor, Windsurf, Cline, Copilot, Gemini**, drop in a one-line adapter from
[`integrations/`](integrations/) — each just points the tool at `AGENTS.md`.

---

MIT — see [LICENSE](LICENSE). · [sage.qorstack.com](https://sage.qorstack.com)
