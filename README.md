# Knowlyx

**Cognitive enforcement layer for AI software development.**

AI coding tools generate code fast — but they don't understand your system. They duplicate utilities, ignore conventions, miss cross-service impact, and hallucinate imports. Knowlyx makes AI agents *understand* your codebase before they touch it.

> Knowledge is passive. Cognition must be enforced.

[![PyPI](https://img.shields.io/pypi/v/knowlyx)](https://pypi.org/project/knowlyx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

- [What it does](#what-it-does)
- [Try the live tutorial](#try-the-live-tutorial)
- [Install](#install)
- [Connect your AI assistant](#connect-your-ai-assistant)
- [5-minute first session](#5-minute-first-session)
- [Multi-repo workspace setup](#multi-repo-workspace-setup)
- [Share knowledge with team via git](#share-knowledge-with-team-via-git)
- [Daily workflow](#daily-workflow)
- [Why Knowlyx](#why-knowlyx)
- [How it works](#how-it-works)
- [Design properties](#design-properties)
- [Troubleshooting](#troubleshooting)
- [Roadmap & docs](#roadmap--docs)

---

## What it does

When you ask Claude *"add password reset flow"*, Knowlyx intercepts and returns:

```text
Domain:    auth (CRITICAL)
Decision:  WARN — follow required workflow before proceeding

Impact:    auth-service, notification-worker, audit-log
Cascade:   account enumeration, email bombing, token replay

Reuse:     EmailTemplate.tsx, useRateLimit hook, AuditLogger
Memory:    "Team uses SendGrid + SES fallback" (approved by alice@co 2 weeks ago)
           [3 more entries auto-synthesized by AI into a single narrative]

Workflow:
  1. Single-use token (15 min expiry)
  2. Rate limit per email + per IP
  3. Audit log every step
  4. Integration test with mock SMTP

Risk policy: Knowlyx decision is authoritative. You may UPGRADE risk
based on context. You may NEVER downgrade.
```

Claude reads this through MCP — it can't skip it. Result: first-try correct code.

---

## Try the live tutorial

A complete 3-repo demo (knowledge + backend service + frontend website) with real code and commits showing the full Knowlyx loop:

```bash
# 1. Install knowlyx (30 seconds, one-time)
curl -fsSL https://raw.githubusercontent.com/knowlyx/knowlyx/main/install.sh | bash
# Windows: irm https://raw.githubusercontent.com/knowlyx/knowlyx/main/install.ps1 | iex

# 2. Clone the shared knowledge into the expected path
git clone https://github.com/SatangBudsai/tutorial-knowlyx-knowledge.git \
  ~/.knowlyx/workspaces/tutorial

# 3. Clone the two product repos anywhere
mkdir -p ~/code && cd ~/code
git clone https://github.com/SatangBudsai/tutorial-knowlyx-service.git
git clone https://github.com/SatangBudsai/tutorial-knowlyx-website.git

# 4. Register MCP with Claude Code in each product repo
cd tutorial-knowlyx-service  && claude mcp add knowlyx -- uvx knowlyx mcp --repo .
cd ../tutorial-knowlyx-website && claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

Then open the WALKTHROUGH:
**[tutorial-knowlyx-knowledge/WALKTHROUGH.md](https://github.com/SatangBudsai/tutorial-knowlyx-knowledge/blob/main/WALKTHROUGH.md)**

What you'll see (across 8 commits):

- Tech lead scaffolds workspace + records 3 kickoff decisions
- Alice scaffolds FastAPI service → Claude auto-applies memory (idempotency, decimal money)
- Bob scaffolds Next.js storefront → Claude follows team conventions (TanStack Query, no raw fetch)
- Bob attempts checkout (HIGH risk) → Knowlyx blocks until tech lead approves
- AI synthesizes the billing domain (4 entries → 1 narrative) — cached for next session

---

## Install

### One-line installer

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/knowlyx/knowlyx/main/install.sh | bash
```

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/knowlyx/knowlyx/main/install.ps1 | iex
```

### One-line installer + workspace + Claude Code in one shot

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/knowlyx/knowlyx/main/install.sh \
  | bash -s -- --workspace my-product --claude --repo .
```

**Windows:**

```powershell
$env:KNOWLYX_WORKSPACE="my-product"; $env:KNOWLYX_CLAUDE="1"
irm https://raw.githubusercontent.com/knowlyx/knowlyx/main/install.ps1 | iex
```

### Manual install (if you prefer)

```bash
# Option A — uv tool (recommended, isolates the install)
uv tool install knowlyx

# Option B — pipx
pipx install knowlyx

# Option C — uvx (no install, runs on demand)
uvx knowlyx --version
```

Requires Python 3.11+. The installer will install `uv` for you if it's missing.

---

## Connect your AI assistant

### Claude Code (one-liner)

```bash
claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

Verify:

```bash
claude mcp list
# → knowlyx ✓
```

### Cursor

Edit `~/.cursor/mcp.json`:

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

Restart Cursor.

### Cline (VS Code)

VS Code Settings → search "cline mcp" → add:

```json
{
  "cline.mcpServers": {
    "knowlyx": {
      "command": "uvx",
      "args": ["knowlyx", "mcp", "--repo", "."]
    }
  }
}
```

### Continue.dev

Edit `~/.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "uvx",
          "args": ["knowlyx", "mcp", "--repo", "."]
        }
      }
    ]
  }
}
```

### Windsurf / Zed / Codex / any MCP client

Same JSON pattern:

```json
{ "command": "uvx", "args": ["knowlyx", "mcp", "--repo", "."] }
```

### No AI assistant — just CLI

```bash
knowlyx scan .
knowlyx analyze "add password reset" --repo .
```

Knowlyx works standalone too — useful as a code review checklist and team decision log.

---

## 5-minute first session

```bash
# 1. Verify install
knowlyx --version

# 2. Scan your project (3 sec → mental model)
cd /path/to/your/project
knowlyx scan .

# 3. Run a cognition request
knowlyx analyze "add rate limiting to /login" --repo .

# 4. (Optional) Save a team decision
knowlyx memory decide auth \
  "Rate limit /login" \
  --body "5 attempts per email per 15min, plus 20 attempts per IP per hour. Use Redis sliding window."

# 5. Verify Claude/Cursor picks it up
# In Claude Code: type "rate limit login" and watch it call analyze_intent + recall_context
```

---

## Multi-repo workspace setup

Real products span multiple repos (api, web, mobile, worker, admin). Knowlyx tracks them as a single **workspace** with shared memory.

### Tech lead (once)

```bash
# 1. Create the central workspace
knowlyx workspace create my-product

# 2. Edit topology
# macOS/Linux:
$EDITOR ~/.knowlyx/workspaces/my-product/workspace.toml
# Windows:
notepad $env:USERPROFILE\.knowlyx\workspaces\my-product\workspace.toml
```

Paste:

```toml
name = "my-product"

[[repos]]
name = "api"
path = "../code/api"
role = "backend"
domains = ["billing", "auth"]
critical = true

[[repos]]
name = "web"
path = "../code/web"
role = "frontend"
domains = ["checkout"]

[[repos]]
name = "worker"
path = "../code/worker"
role = "worker"

[[dependencies]]
from = "web"
to = "api"
type = "api"

[[dependencies]]
from = "worker"
to = "api"
type = "event"
```

### Each developer (per repo)

```bash
cd ~/code/api
knowlyx init --link my-product \
  --remote git@github.com:your-org/my-product-knowledge.git
# auto-detects role + domains from package.json/pyproject.toml/etc
# writes .knowlyx/config.toml — commit this to git
git add .knowlyx/config.toml
git commit -m "link to knowlyx workspace"
```

The `--remote` flag records the URL of the shared knowledge repo inside
`.knowlyx/config.toml`. When teammates clone `api`, Knowlyx already knows where
to fetch the shared brain from — and prints the exact `git clone` command if
the local workspace folder is missing.

Now every dev who clones `api` is automatically connected to `my-product`'s shared memory.

---

## Share knowledge with team via git

`~/.knowlyx/workspaces/my-product/` is just a folder of JSON + TOML. Push it to GitHub / GitLab / self-hosted — no infra needed.

### Tech lead — git init + push

```bash
knowlyx sync init \
  --workspace my-product \
  --remote git@github.com:your-org/my-product-knowledge.git

knowlyx sync push --workspace my-product -m "init"
```

### Each developer — clone shared knowledge

When you clone a project repo that's already linked, Knowlyx prints the exact
clone command on first use — you don't have to look up the URL:

```text
$ knowlyx memory list
ℹ Shared knowledge for workspace 'my-product' is not on this machine.
  Run:  git clone git@github.com:your-org/my-product-knowledge.git \
                  ~/.knowlyx/workspaces/my-product
```

Copy that command and run it. Done.

(The URL lives in each linked repo's `.knowlyx/config.toml` as
`knowledge_remote`, so it travels with the repo.)

Auth: uses your existing git auth (SSH key / HTTPS credential helper / `gh auth`). No Knowlyx-specific tokens needed.

Full setup including self-hosted GitLab, conflict resolution, and permissions:
**[docs/git-sync.md](docs/git-sync.md)**

### Concurrency safety

All writes to `memory.json` and `approvals.json` are protected by:

- **Cross-platform file lock** (`fcntl` POSIX / `msvcrt` Windows)
- **Atomic write** (write temp + `os.replace()`)
- **Read-modify-write under lock** — concurrent saves never lose updates

**Approve/reject fail-safe:** once an approval is REJECTED, it stays rejected. Subsequent approves are no-ops. Same rule applies in git sync conflict resolution.

---

## Daily workflow

```bash
# Pull latest decisions before starting
knowlyx sync pull --workspace my-product

# Work normally — Claude/Cursor calls Knowlyx tools automatically.
# When you make important decisions, save them:
knowlyx memory decide billing \
  "Use Stripe for subscriptions" \
  --body "Stripe Billing for B2C, manual invoice for B2B over \$10k"

# Push at end of day
knowlyx sync push --workspace my-product -m "decisions from billing redesign"
```

Recommended aliases (`.bashrc` / `.zshrc`):

```bash
alias kw-pull='knowlyx sync pull --workspace my-product'
alias kw-push='knowlyx sync push --workspace my-product'
alias kw='knowlyx'
```

---

## Why Knowlyx

| Pain that every team has | Knowlyx solution |
|---|---|
| "We already have a helper for that" — duplicate utils | `get_reusable_assets` injects existing code |
| AI ignores CLAUDE.md / .cursorrules | MCP tool result — AI trusts tools more than markdown |
| Migration breaks downstream services | `get_cross_repo_impact` shows blast radius |
| AI hallucinates imports/functions | `validate_generated_code` blocks before write |
| Refactor misses call sites | `get_impact_analysis` lists every caller |
| 2-week onboarding for new devs | `scan + graph` = 5-min mental model |
| Silent API contract breakage | Risk gate + deprecation workflow |
| AI re-invents same decision team made last month | `get_domain_knowledge` + cached AI synthesis |
| AI downgrades risk to ship faster | Risk policy: `proceed → warn → ask → reject`, upgrade-only |

---

## How it works

**No LLM inside Knowlyx — by design.** Knowlyx is 100% rule-based + pattern matching + graph algorithms. Deterministic, fast (<100ms), free, offline, auditable.

The intelligence comes from your AI agent (Claude/Cursor/etc.): Knowlyx hands the agent **structured cognition data** through MCP, the agent does the reasoning and writing.

For tasks that need judgment (summarizing related memory, weighing historical risk):

1. Knowlyx returns raw data + a structured instruction for the AI
2. The AI agent does the synthesis using its own LLM
3. Knowlyx caches the result (`save_synthesis`) so future sessions reuse it
4. New evidence automatically marks the cache stale → triggers re-synthesis

Risk decisions follow the **upgrade-only rule**: the AI can make Knowlyx's decision stricter (`proceed → warn → ask → reject`), but never looser.

```text
┌─────────────────────────────────────────────────┐
│  AI Agent (Claude / Cursor / Cline / Codex)     │
└──────────────────┬──────────────────────────────┘
                   │ MCP protocol — 25 tools
┌──────────────────▼──────────────────────────────┐
│  ENFORCEMENT (mcp/server.py)                    │
│  • analyze_intent  • get_conventions            │
│  • get_reusable_assets  • get_impact_analysis   │
│  • get_domain_knowledge  • save_synthesis       │
│  • assess_risk_in_context  • get_module_context │
│  • validate_generated_code  • request_approval  │
│  • recall_context  • get_workspace_context  …   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  REASONING — Intent → Impact → Risk → Decision  │
│  (rule-based, deterministic, no LLM)            │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┼───────────────────┐
       ▼           ▼                   ▼
┌──────────┐ ┌──────────────┐    ┌──────────┐
│  GRAPH   │ │   MEMORY     │    │  PACKS   │
│ NetworkX │ │ schema v2    │    │ 7 built  │
│ cascade  │ │ + AI synth   │    │   -in    │
│ rules    │ │ + file lock  │    │ domains  │
└────┬─────┘ └──────────────┘    └──────────┘
     │
┌────▼────────────────────────────────────────────┐
│  SCANNER — language/framework/architecture/     │
│  domains/conventions/reusable assets            │
└─────────────────────────────────────────────────┘
```

### Memory schema v2

```json
{
  "version": 2,
  "entries": { "<id>": { kind, domain, title, body, approved, ... } },
  "syntheses": {
    "<domain>": {
      "summary": "narrative tying related decisions together",
      "key_themes": [...],
      "open_questions": [...],
      "stale": false
    }
  }
}
```

v1 (flat dict) files auto-migrate on first read. New entries automatically mark their domain's synthesis stale → next AI session re-synthesizes.

---

## Design properties

These are guarantees Knowlyx makes by construction:

| Property | Why it matters |
|---|---|
| **Deterministic** | Same input → same output every time. Audits and CI gates work. |
| **Fast** (<100ms reasoning) | Pre-commit hooks stay usable. AI doesn't wait. |
| **Free** ($0 to run) | No API costs. No surprise bills. |
| **Offline** | Works air-gapped, in CI, on planes. |
| **No vendor lock-in** | Works with any MCP client. No required LLM provider. |
| **Concurrent-safe** | Multiple devs/sessions can save simultaneously without lost updates. |
| **Audit-friendly** | Git log shows every memory/approval change with author + timestamp. |
| **Backward compatible** | Schema migrations are automatic. Old files keep working. |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `knowlyx: command not found` | uv path not loaded | Open new terminal, or `source ~/.bashrc` |
| `Workspace '<name>' not found` | Knowledge repo not cloned at the expected path | Must be `~/.knowlyx/workspaces/<workspace-name>` exactly |
| Claude doesn't see memory | Local clone of knowledge repo is stale | `cd ~/.knowlyx/workspaces/<name> && git pull` |
| `git push` rejected | Behind remote | `knowlyx sync pull` first, then push |
| `memory.json` git conflict | Two devs saved at the same time | `knowlyx sync pull` auto-merges by timestamp; manual edit if not |
| `Permission denied (publickey)` | SSH key not registered | Add `~/.ssh/id_ed25519.pub` to GitHub Settings → SSH keys |
| Approval not unlocking AI | Status still pending | `knowlyx approval list` → `knowlyx approval approve <id>` |
| TypeScript errors in fresh website clone | `node_modules` missing | `npm install` |

---

## Roadmap & docs

- **[ROADMAP.md](ROADMAP.md)** — versions + what's next
- **[CHANGELOG.md](CHANGELOG.md)** — every release
- **[docs/quickstart.md](docs/quickstart.md)** — 5-minute first session
- **[docs/cli.md](docs/cli.md)** — every CLI command
- **[docs/mcp.md](docs/mcp.md)** — MCP integration details
- **[docs/architecture.md](docs/architecture.md)** — 6 layers explained
- **[docs/multi-repo.md](docs/multi-repo.md)** — `knowlyx.toml` + cross-repo impact
- **[docs/distributed-knowledge.md](docs/distributed-knowledge.md)** — central store + per-repo link + concurrency
- **[docs/git-sync.md](docs/git-sync.md)** — share workspace via GitHub/GitLab (full step-by-step)
- **[docs/usage-examples.md](docs/usage-examples.md)** — 7 real-world scenarios
- **[docs/cognition-packs.md](docs/cognition-packs.md)** — built-in domain knowledge
- **[Live tutorial](https://github.com/SatangBudsai/tutorial-knowlyx-knowledge/blob/main/WALKTHROUGH.md)** — 3-repo working demo

---

## Contribute

PRs welcome — see **[CONTRIBUTING.md](CONTRIBUTING.md)**.

```bash
git clone https://github.com/knowlyx/knowlyx
cd knowlyx
uv sync --extra dev
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE).
