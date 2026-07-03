# Sage integrations — one protocol, every agent

The protocol lives in **[`../AGENTS.md`](../AGENTS.md)** and every command's full
body lives once under **[`../agents/sage/commands/`](../agents/sage/commands/)**.
The files in this folder are **thin adapters** — each just points its tool at the
canonical files. Copy only what your tool needs (or run the one-command installer
in the root README, which does the detection for you).

## Usage

```bash
# Claude Code
cp -r integrations/.claude .

# Cursor
cp -r integrations/.cursor .

# Windsurf
cp -r integrations/.windsurf .

# Cline
cp -r integrations/.clinerules .

# GitHub Copilot
cp -r integrations/.github .

# Codex
cp -r integrations/.codex .

# Gemini CLI
cp integrations/gemini.md ./GEMINI.md
```

## What gets placed

| Copy           | Destination             | For            |
| -------------- | ----------------------- | -------------- |
| `.claude/`     | `.claude/commands/`     | Claude Code    |
| `.cursor/`     | `.cursor/rules/`        | Cursor         |
| `.windsurf/`   | `.windsurf/rules/`      | Windsurf       |
| `.clinerules/` | `.clinerules/`          | Cline          |
| `.github/`     | `.github/instructions/` | GitHub Copilot |
| `.codex/`      | `.codex/prompts/`       | Codex          |
| `gemini.md`    | `GEMINI.md`             | Gemini CLI     |

**OpenCode, Google Antigravity** (and Codex) read `AGENTS.md` natively — the
adapters above just add the slash-command entry points. Keep `AGENTS.md` at your
repo root either way.

Each adapter is intentionally tiny: it points at `AGENTS.md` and the canonical
command under `agents/sage/commands/`. Edit the protocol or a command in **one**
place and every agent stays in step.

## Commands included

| Command                 | What it does                                                        |
| ----------------------- | ------------------------------------------------------------------- |
| `/sage`                 | Run the cognition pipeline + run checklist before any code change   |
| `/sage-flow`            | Turn a feature/journey into an implementation-ready business flow   |
| `/sage-unit-test`       | Write unit tests that match how this repo already tests             |
| `/sage-n2n-test`        | Drive the app end-to-end (Playwright/k6/…) and prove the flow       |
| `/sage-security-review` | Review a change for real, exploitable security holes                |
| `/sage-docs`            | Turn any document into a plain-Markdown flow doc (`docs/<slug>.md`) |
| `/sage-learning`        | Scan the codebase and capture team knowledge to `agents/sage/`      |
| `/sage-search-skill`    | Research current best practices for this stack and write skills     |

`/sage` is the one you use most — its §0 checklist decides which of the others to
run, asks you to confirm, then runs them for you.

> Don't see your agent? Most modern agents support either `AGENTS.md` or a
> rules/instructions file — point it at `AGENTS.md` the same way.
