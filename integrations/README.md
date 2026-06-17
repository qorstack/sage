# Sage integrations — one protocol, every agent

The protocol lives in **[`../AGENTS.md`](../AGENTS.md)** (single source of truth).
Many agents read `AGENTS.md` directly. For the ones that look elsewhere, drop the
matching thin adapter below into your repo — it just routes that tool to
`AGENTS.md`, so there's nothing to keep in sync.

| Agent | Reads `AGENTS.md` natively? | Adapter → copy to your repo as |
| --- | --- | --- |
| **Claude Code** | yes (also `CLAUDE.md`) | — (keep `AGENTS.md` at root) |
| **OpenAI Codex** | yes | — |
| **OpenCode** | yes | — |
| **Google Antigravity** | yes | — |
| **Cursor** | no | [`cursor.mdc`](cursor.mdc) → `.cursor/rules/sage.mdc` |
| **Windsurf** | no | [`windsurf.md`](windsurf.md) → `.windsurf/rules/sage.md` |
| **Cline** | no | [`cline.md`](cline.md) → `.clinerules/sage.md` |
| **GitHub Copilot** | no | [`copilot.md`](copilot.md) → `.github/copilot-instructions.md` |
| **Gemini CLI** | no | [`gemini.md`](gemini.md) → `GEMINI.md` |

Each adapter is intentionally tiny: "read and follow `AGENTS.md`." Edit the
protocol in one place (`AGENTS.md`) and every agent stays in step.

> Don't see your agent? Most modern agents support either `AGENTS.md` or a
> rules/instructions file — point it at `AGENTS.md` the same way.
