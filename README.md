# knowai

![knowai](assets/logo-full.png)

**Cognitive enforcement layer for AI software development.**

> Knowledge is passive. Cognition must be enforced.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What it does

AI assistants generate code fast but don't understand your system — they duplicate utilities, miss conventions, and re-invent decisions.

knowai sits between Claude / Cursor and your repo. Via MCP, it returns:

```text
Domain:    payment (HIGH)
Decision:  WARN — follow team conventions
Reuse:     PaymentClient, IdempotencyMiddleware
Memory:    "Use idempotency keys" (alice, approved)
Risk:      refund → webhook → ledger
```

AI-written entries land as **Pending** until a human approves them on the dashboard.

---

## How knowai differs from generic knowledge tools

| Dimension       | RAG / Vector KB          | Generic Knowledge Graph | **knowai**                                                          |
| --------------- | ------------------------ | ----------------------- | ------------------------------------------------------------------- |
| Knowledge shape | text chunks + embeddings | static nodes/edges      | **Cognitive Graph** — domain × asset × convention × impact edge     |
| When AI uses it | pulled at prompt time    | queried only when asked | **Mandatory call before any code change** (`analyze_intent`)        |
| Who decides     | LLM decides              | LLM interprets          | **Rule-based engine** returns `proceed` / `warn` / `ask` / `reject` |
| Team knowledge  | none / mixed in          | write your own schema   | `remember_team_decision` + approval queue                           |
| Impact / risk   | none                     | manual queries          | **Blast radius + risk level computed automatically**                |
| Enforcement     | passive                  | passive                 | **MCP-first + audit** — AI cannot skip it                           |

> RAG and KGs are **a library**. knowai is **a checkpoint before code is written.**

### Accuracy in practice

Higher on real codebases — AI stops reinventing utilities, matches team style, and won't contradict past decisions. Risky changes are blocked before code is written.

Doesn't help much on greenfield / one-shot scripts with no team context.

### The more you use it, the less it costs

**Cheaper over time** — because the AI gets more accurate the longer you use it:

- Reuses approved team decisions instead of re-deriving them every session
- Stops writing code that gets rejected and rewritten (the biggest token sink)
- Catches risky changes before code is generated, not after
- Pulls only the relevant assets / conventions for each request, not the whole repo

A small upfront investment makes this possible: seed memory once with `/knowai-generate`, then let every `/knowai` call run the full pipeline so each change starts from real context.

---

## Prerequisites

- Docker + Docker Compose v2 (the published image supports `linux/amd64` and `linux/arm64`, so Apple Silicon Macs work natively)
- Python 3.11+ with [`uv`](https://docs.astral.sh/uv/) (only for Part 2). Install it:
  - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`)
  - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- ~2GB free RAM

---

## Part 1 — Dashboard

### 1. Create `.env`

```env
POSTGRES_USER=knowais
POSTGRES_PASSWORD=knowai
POSTGRES_DB=knowai
POSTGRES_PORT=5432
WEB_PORT=8080
```

### 2. Create `docker-compose.yml`

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: knowai-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports: ["${POSTGRES_PORT}:5432"]
    volumes: [knowai_pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
      interval: 5s

  web:
    image: ghcr.io/qorstack/knowai:latest
    container_name: knowai-web
    depends_on: { postgres: { condition: service_healthy } }
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
    ports: ["${WEB_PORT}:8080"]

volumes:
  knowai_pgdata:
```

### 3. Start & open

```bash
docker compose up -d
open http://localhost:8080
```

Use the dashboard to add knowledge entries by hand. Done — or continue to Part 2 for AI integration.

---

## Part 2 — AI integration

### 4. Install the CLI

Install [`uv`](https://docs.astral.sh/uv/), then the CLI:

On macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env
uv tool install git+https://github.com/qorstack/knowai.git
knowai --version
```

On Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# close & reopen PowerShell so PATH refreshes, then:
uv tool install git+https://github.com/qorstack/knowai.git
knowai --version
```

> `uv: command not found` after install? Run `source $HOME/.local/bin/env` (mac/Linux) or reopen the terminal (Windows). To make it permanent on mac/Linux: `echo '. "$HOME/.local/bin/env"' >> ~/.zshrc`.

### 5. Create `knowai.config` at each repo root

```toml
workspace = "my-product"
repo_name = "aaa-api"

[database]
host     = "localhost"
port     = 5432
user     = "knowai"
password = "knowai"
db       = "knowai"
schema   = "public"
```

> Or put `[database]` in `~/.knowai.config` once and per-repo files only need `workspace` + `repo_name`.

When Claude saves memory via MCP, knowai auto-tags it with `scope=workspace`, this `workspace`, and this `repo_name` — entries land in the right bucket on the dashboard without any extra work.

### 6. Register knowai with Claude Code

Need Claude Code first? Install it from [claude.com/claude-code](https://claude.com/claude-code) (`npm install -g @anthropic-ai/claude-code`). Then:

```bash
claude mcp add --scope user knowai -- knowai mcp
claude mcp list   # should show: knowai ✓
```

### 7. Install the slash commands

```bash
knowai install-claude-commands     # copies /knowai and /knowai-generate to ~/.claude/commands/
```

Two commands ship:

| Command             | Use it when                                                                                                                                                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/knowai <request>` | **Every feature / refactor / fix.** Forces Claude to run the full pipeline (analyze_intent → recall_context → get_reusable_assets → assess_risk_in_context) and open with a `Risk:` / `Decision:` header before writing code. |
| `/knowai-generate`  | **Once, then occasionally.** Have Claude read this repo and seed meaningful memory entries. Safe to re-run after refactors.                                                                                                   |

> Why a slash command? MCP tool descriptions only reach Claude when it _decides_ to use a tool — a plain prompt can slip past the pipeline. `/knowai` makes the consult mandatory.

### 8. Seed memory from the repo (first time or re-generate)

Open Claude inside the repo and run:

```text
/knowai-generate
```

Claude will walk the codebase, extract meaningful conventions / decisions / reusable assets, and save them through MCP. Entries land as **Pending** for you to approve on the dashboard.

Re-run after a big refactor or when onboarding a new repo — it's idempotent.

> Add `.knowai/` to your repo's `.gitignore`

### 9. Use it

In Claude, try:

```text
/knowai add a refund endpoint to /payments
```

You should see a reply that opens with `Risk: <level> — <why>` / `Decision: ...` and references your stored memory in the `Memory:` line.

If not: `claude mcp list` shows `✗` → run `knowai mcp` in a terminal to see the error (usually missing DB credentials).

---

## Dashboard at a glance

- **Home** — two hero cards: ⏳ **Pending review** (AI entries awaiting approval) + 🌐 **Global knowledge**. Plus a per-workspace breakdown.
- **Knowledge** — workspace pills at the top, then filter by source (Human / AI), status (Approved / Pending), or domain. Every row shows scope + source badges.
- **Entry detail** — full metadata strip plus a **Move to Global ↑** / **Move to Workspace ↓** button so you can re-scope without re-creating.
- **Summaries / Activity** — per-domain AI syntheses and full audit log.

---

## Tips — fewer tokens, sharper answers

- **Use `/knowai` only for real changes** — features, refactors, bug fixes. Skip it for renames, typos, formatting.
- **Approve memory on the dashboard** — pending entries are not recalled in the next session. Approved ones are.
- **Run `/knowai-generate` once per repo** — re-run only after a big refactor or new domain. It's not a routine task.
- **Set `repo_name` precisely** in `knowai.config` — scopes recall tighter, so Claude pulls less but more relevant context.
- **Forget stale memory** — outdated decisions waste tokens and confuse Claude. Use `knowai memory forget <id>` or the dashboard.

---

## Updating

```bash
# Upgrade the CLI + MCP server
uv tool upgrade knowai

# Then restart Claude Code so it reloads the MCP subprocess
# (the old version is cached until restart)

# Upgrade the dashboard
docker compose pull web && docker compose up -d
```

Stop / wipe:

```bash
docker compose stop                # keep data
docker compose down -v             # wipe all data
```

---

MIT — see [LICENSE](LICENSE).
