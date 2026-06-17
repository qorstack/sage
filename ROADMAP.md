# Roadmap

Sage is a single-file cognition protocol ([`AGENTS.md`](AGENTS.md)) plus
Markdown knowledge ([`agents/sage/`](agents/sage/)). The roadmap is
about making the protocol sharper and reaching more agents — not about building
software.

## Now

- Tighten and clarify the protocol in `AGENTS.md`.
- Expand starter knowledge: more domains and example `decisions/`.
- More agent adapters in [`integrations/`](integrations/) as new tools appear.

## Next

- A small, optional **validator** (lint frontmatter / find broken links / flag
  conflicting rules) — itself runnable by any agent reading a short spec, no
  install required.
- Worked **examples**: real repos showing `agents/sage/` trees.
- A richer **conflict/synthesis** convention (how the agent reconciles two rules
  that disagree) documented in `AGENTS.md`.

## Maybe

- A hosted starter-knowledge gallery (copy a domain pack into your repo).
- Conventions for cross-repo knowledge sharing (one knowledge repo, many repos).

## History

A previous Python implementation (MCP server, CLI, stores, dashboard) was
removed in favor of this single-file model — recoverable from git history.

## Influence the roadmap

Open a [GitHub Discussion](https://github.com/qorstack/sage/discussions) —
concrete use cases drive priority.
