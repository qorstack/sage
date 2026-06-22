# Sage integrations — one protocol, every agent

The protocol lives in **[`../AGENTS.md`](../AGENTS.md)** (single source of truth).
This folder mirrors what goes in your repo root — copy only what your tool needs.

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

# Gemini CLI
cp integrations/GEMINI.md .
```

## What gets placed

| Copy | Destination | For |
| --- | --- | --- |
| `.claude/` | `.claude/commands/` | Claude Code |
| `.cursor/` | `.cursor/rules/` | Cursor |
| `.windsurf/` | `.windsurf/rules/` | Windsurf |
| `.clinerules/` | `.clinerules/` | Cline |
| `.github/` | `.github/instructions/` | GitHub Copilot |
| `GEMINI.md` | `GEMINI.md` | Gemini CLI |

**OpenAI Codex, OpenCode, Google Antigravity** read `AGENTS.md` natively —
no adapter needed, just keep `AGENTS.md` at your repo root.

Each adapter is intentionally tiny: "read and follow `AGENTS.md`." Edit the
protocol in one place and every agent stays in step.

## Commands included

| Command | What it does |
| --- | --- |
| `/sage` | Run the cognition pipeline before any code change |
| `/sage-learning` | Scan the codebase and capture team knowledge to `agents/sage/` |
| `/sage-search-skill` | Research current best practices for this stack and write them as skills |
| `/sage-docs` | Turn any document into a styled HTML file (`docs/`) with a Mermaid diagram |

> Don't see your agent? Most modern agents support either `AGENTS.md` or a
> rules/instructions file — point it at `AGENTS.md` the same way.
