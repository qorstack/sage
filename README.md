# Knowlyx

**Cognitive enforcement layer for AI software development.**

AI coding tools generate code fast — but they don't understand your system. They duplicate utilities, ignore your conventions, miss cross-service impact, and hallucinate imports. Knowlyx makes AI agents *understand* your codebase before they touch it.

> Knowledge is passive. Cognition must be enforced.

[![PyPI](https://img.shields.io/pypi/v/knowlyx)](https://pypi.org/project/knowlyx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What it does

When you ask Claude *"add password reset flow"*, Knowlyx intercepts:

```text
Domain:    auth (CRITICAL)
Action:    add
Impact:    auth-service, notification-worker, audit-log
Cascade:   account enumeration risk, email bombing, token replay
Decision:  WARN — follow required workflow

Reuse:     EmailTemplate.tsx, useRateLimit hook, AuditLogger
Memory:    "Team uses SendGrid + SES fallback" (approved 2 weeks ago)
Workflow:
  1. Single-use token (15 min expiry)
  2. Rate limit per email + per IP
  3. Audit log every step
  4. Integration test with mock SMTP
```

Claude reads this through MCP — it can't skip it. Result: first-try correct code.

## Install

### Claude Code (one-liner)

```bash
claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

### Cursor / Cline / other MCP clients

Add to your MCP config:

```json
{
  "mcpServers": {
    "knowlyx": {
      "command": "uvx",
      "args": ["knowlyx", "mcp", "--repo", "."]
    }
  }
}
```

### Standalone CLI

```bash
pipx install knowlyx
# or
uv tool install knowlyx
```

## Quick start

```bash
# Scan a repo (3 seconds → mental model)
knowlyx scan .

# Analyze a request before coding
knowlyx analyze "rename users.email column" --repo .

# List reusable assets before creating new code
knowlyx assets billing --repo .

# Show built-in cognition for a domain
knowlyx pack auth
```

## Why Knowlyx

| Pain that every team has | Knowlyx solution |
|---|---|
| "We already have a helper for that" — duplicate utils | `get_reusable_assets` injects existing code first |
| AI ignores CLAUDE.md / .cursorrules | MCP tool result — AI trusts tools more than markdown |
| Migration breaks downstream services | `get_cross_repo_impact` shows blast radius |
| AI hallucinates imports/functions | `validate_generated_code` blocks before write |
| Refactor misses call sites | `get_impact_analysis` lists every caller |
| 2-week onboarding for new devs | `scan + graph` = 5-min mental model |
| Silent API contract breakage | Risk gate + deprecation workflow |

## Multi-repo support

Real products span multiple repos (api, web, mobile, worker, admin). Knowlyx tracks them as a **workspace** with shared memory:

```bash
knowlyx workspace create my-product
cd ~/code/api && knowlyx link my-product --role backend --critical
cd ~/code/web && knowlyx link my-product --role frontend
```

Memory + decisions + approvals are stored once in `~/.knowlyx/workspaces/my-product/` and shared across every repo linked to it.

Sync the workspace via git (zero infra needed) — see [git-sync guide](docs/git-sync.md).

## Documentation

- [Quick start](docs/quickstart.md) — install + first session
- [CLI reference](docs/cli.md) — every command
- [MCP integration](docs/mcp.md) — Claude, Cursor, Cline setup
- [Architecture](docs/architecture.md) — how the layers fit together
- [Multi-repo workspace](docs/multi-repo.md) — knowlyx.toml + cross-repo impact
- [Distributed knowledge](docs/distributed-knowledge.md) — central store + per-repo links
- [Git sync](docs/git-sync.md) — share workspace via GitHub/GitLab
- [Usage examples](docs/usage-examples.md) — 7 real-world scenarios
- [Cognition packs](docs/cognition-packs.md) — built-in domain knowledge

## Roadmap

See [ROADMAP.md](ROADMAP.md). High-level:

- ✅ **v0.1** — Scanner + Reasoning + 8 MCP tools
- ✅ **v0.2** — Memory (file + Qdrant) + 7 Cognition Packs
- ✅ **v0.3** — Workspace + Graph export + Approval queue
- ✅ **v0.4** — Distributed knowledge (central store + link)
- 🟡 **v0.5** — Git sync + AI self-review + commit hooks
- 🔵 **v1.0** — Frontend UI + Design cognition + ML risk scoring

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/knowlyx/knowlyx
cd knowlyx
uv sync
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE).
