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
- [Team setup (multi-developer)](#team-setup-multi-developer)
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
curl -fsSL https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.sh | bash
# Windows: irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex

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
curl -fsSL https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.sh | bash
```

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex
```

### One-line installer + workspace + Claude Code in one shot

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.sh \
  | bash -s -- --workspace my-product --claude --repo .
```

**Windows:**

```powershell
$env:KNOWLYX_WORKSPACE="my-product"; $env:KNOWLYX_CLAUDE="1"
irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex
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

## Team setup (multi-developer)

Real products span multiple repos and multiple devs. Knowlyx is a **per-machine CLI tool** — every dev installs it locally, then connects to the same central workspace (a git repo holding the shared memory).

### 👑 Tech Lead — once per product

```powershell
# 1. Install knowlyx (Windows; macOS/Linux equivalents in the Install section)
irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex

# 2. Create the central workspace
knowlyx workspace create my-product

# 3. Push it to a private git repo (any host — GitHub/GitLab/self-host)
cd $env:USERPROFILE\.knowlyx\workspaces\my-product
git init && git branch -M main && git add . && git commit -m "init"
git remote add origin git@github.com:your-org/my-product-knowledge.git
git push -u origin main
```

That's the entire tech-lead setup. The `workspace.toml` topology auto-fills as each dev links their repo — you don't have to declare `[[repos]]` by hand.

### 👨‍💻 Each developer — same commands for everyone

```powershell
# 1. Install knowlyx (one-time, same as tech lead)
irm https://raw.githubusercontent.com/SatangBudsai/knowlyx/main/install.ps1 | iex

# 2. Clone the project repo you'll work on
git clone git@github.com:your-org/api.git
cd api

# 3. Link this repo to the workspace
knowlyx init --link my-product \
  --remote git@github.com:your-org/my-product-knowledge.git

# 4. Knowlyx auto-detects role + domains, auto-registers in workspace.toml.
# If the shared knowledge isn't on this machine yet, it prints the exact
# clone command — copy/paste and run it.
git clone git@github.com:your-org/my-product-knowledge.git \
          ~/.knowlyx/workspaces/my-product

# 5. Wire up Claude Code (or Cursor/Cline/etc.) — once per repo
claude mcp add knowlyx -- uvx knowlyx mcp --repo .

# 6. Commit the link config so the next dev who clones is auto-connected
git add .knowlyx/config.toml && git commit -m "link to knowlyx workspace" && git push
```

**~3 minutes from clone to working** — no docs to read; Knowlyx prints any missing setup steps as you go.

### Daily workflow

```bash
# Morning — pull the team's latest decisions
git -C ~/.knowlyx/workspaces/my-product pull

# Work normally — Claude/Cursor calls Knowlyx tools through MCP.
# When a meaningful decision is made:
knowlyx memory decide billing "Use Stripe for subscriptions" \
  --body "Stripe Billing for B2C, manual invoice for B2B over \$10k"

# End of day — push knowledge back
cd ~/.knowlyx/workspaces/my-product
git add . && git commit -m "decisions from billing redesign" && git push
```

Convenience aliases (add to `.bashrc` / `.zshrc` / PowerShell `$PROFILE`):

```bash
alias kw-pull='git -C ~/.knowlyx/workspaces/my-product pull'
alias kw-push='git -C ~/.knowlyx/workspaces/my-product add -A && git -C ~/.knowlyx/workspaces/my-product commit -m "knowledge update" && git -C ~/.knowlyx/workspaces/my-product push'
```

```powershell
# PowerShell profile
function kw-pull { Push-Location $env:USERPROFILE\.knowlyx\workspaces\my-product; git pull; Pop-Location }
function kw-push { Push-Location $env:USERPROFILE\.knowlyx\workspaces\my-product; git add -A; git commit -m "knowledge update"; git push; Pop-Location }
```

### Concurrency — what happens when two devs save at once

| Situation | How Knowlyx handles it |
|---|---|
| Two devs save different memory entries simultaneously | ✅ git auto-merges (different IDs, no conflict) |
| Two devs save the same logical decision (ID collision) | ✅ `knowlyx sync pull` auto-merges newer-wins by timestamp |
| Dev A approves, Dev B rejects the same request | ✅ Fail-safe: **REJECTED stays rejected**, even on later approves |
| Two processes write to memory.json simultaneously | ✅ Cross-platform file lock (`fcntl` POSIX / `msvcrt` Windows) + atomic write — no lost updates |

Auth: uses your existing git auth (SSH key / HTTPS credential helper / `gh auth`). No Knowlyx-specific tokens needed. Works with GitHub, GitLab, Gitea, self-hosted Forgejo, etc.

Full deep-dive (self-hosted GitLab, manual conflict resolution, branch protection):
**[docs/git-sync.md](docs/git-sync.md)**

### FAQ

| Question | Answer |
|---|---|
| Does every dev install Knowlyx? | ✅ Yes — it's a CLI tool, per-machine |
| Who creates the workspace? | ✅ Tech lead, once. Then `git push` |
| Do other devs run `workspace create`? | ❌ No — they `git clone` the workspace that tech lead created |
| Does workspace.toml need manual editing? | ❌ No — `knowlyx init --link` auto-registers each repo |
| What if I forget to pull? | ⚠️ You'll save into a stale view; on `git push` you'll need to pull-merge first. Auto-merger handles common cases |

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
git clone https://github.com/SatangBudsai/knowlyx
cd knowlyx
uv sync --extra dev
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE).
