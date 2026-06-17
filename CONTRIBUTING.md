# Contributing to Sage

Thank you for considering contributing! Sage is open source under MIT.

Sage is a **single-file cognition protocol** — it's all Markdown, no code,
no build, no tests to run. Contributing means improving text.

## What you can improve

- **The protocol** — [`AGENTS.md`](AGENTS.md). The source of truth for how agents
  behave. Keep it clear, ordered, and tool-agnostic.
- **Starter knowledge** — [`agents/sage/`](agents/sage/). Add or refine
  domain `rules.md` / `decisions/*.md`. Keep entries small (one idea per file) and
  in the frontmatter shape documented in `AGENTS.md` §2.
- **Agent adapters** — [`integrations/`](integrations/). Add a thin adapter for a
  new agent. It must only route the tool to `AGENTS.md` — never duplicate the
  protocol text.
- **Landing site** — [`landing/index.html`](landing/index.html). Self-contained
  static HTML.

## Ground rules

- **Single source of truth:** don't copy `AGENTS.md`'s wording into adapters or
  the README — link to it.
- **Markdown only:** if a change seems to need a program, it's probably the wrong
  change for this project.
- **Surgical + consistent:** match the surrounding style; one focused change per PR.

## Submitting

Open a [GitHub issue](https://github.com/qorstack/sage/issues) to discuss, or
a PR directly. Since everything is Markdown, review is just reading the diff.

By contributing, you agree your contributions will be licensed under MIT.
