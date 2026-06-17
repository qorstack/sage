# CLAUDE.md

Guidance for AI agents working **on this repository**.

## What this repo is

Sage is a **cognition protocol** for AI coding agents, shipped as a single
declarative file — not a program. There is **no Python, no server, no build**.
The product is:

- **[`AGENTS.md`](AGENTS.md)** — the protocol itself (the source of truth). Edit
  this to change how agents behave: the pre-code pipeline, the knowledge
  convention, conversation-capture, enforcement levels, the risk header.
- **`agents/sage/`** — starter cognition knowledge as Markdown (YAML
  frontmatter + body), organized by domain (`<domain>/rules.md`,
  `<domain>/decisions/<slug>.md`). Human + AI editable, shared via git.
- **`integrations/`** — thin per-agent adapters that point each tool (Cursor,
  Windsurf, Cline, Copilot, Gemini/Antigravity, …) at `AGENTS.md`. Keep them
  thin: they route to `AGENTS.md`, they don't duplicate the protocol.
- **`landing/`** — the static promo site (dark, deployed to GitHub Pages /
  `sage.qorstack.com`). Edit `landing/index.html`.

## Working rules

- **Single source of truth.** The protocol lives in `AGENTS.md`. Don't fork its
  wording into the integration files or the README — point at it.
- **No code.** If a change seems to need Python/tooling, reconsider — the whole
  value here is that it's just Markdown anyone can read, edit, and diff.
- **Keep knowledge entries small and in OKF shape** (frontmatter + one idea per
  file). See `AGENTS.md` §2 for the exact frontmatter fields.
- **Surgical edits, match surrounding style.** Markdown only.

## History

This repo previously shipped a Python implementation (MCP server, CLI, stores,
dashboard). It was removed in favor of the single-file protocol; recover it from
git history if ever needed.
