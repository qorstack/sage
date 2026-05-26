# knowai

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

Storage: **Postgres** with semantic auto-merge. Web dashboard for the team.

---

## Prerequisites

- Docker + Docker Compose v2
- Python 3.11+ with `uv` (only for Part 2)
- ~2GB free RAM

---

## Part 1 — Dashboard

### 1. Create `.env`

```env
POSTGRES_USER=knowai
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
    image: qorstack/knowai:latest
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

```bash
uv tool install git+https://github.com/qorstack/knowai.git
knowai --version
```

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

### 6. Register knowai with Claude Code

```bash
claude mcp add --scope user knowai -- knowai mcp
claude mcp list   # should show: knowai ✓
```

### 7. Seed memory from existing code

```bash
knowai install-claude-commands     # one-time, copies /knowai-generate
```

In Claude Code, run `/knowai-generate` — Claude reads the repo and writes meaningful entries via MCP.

### 8. Verify

In Claude, try: _"Add a refund endpoint to /payments"_ — you should see a `knowai` tool call and a reply that references your stored knowledge.

If not: `claude mcp list` shows `✗` → run `knowai mcp` in a terminal to see the error (usually missing DB credentials).

---

## CLI cheat sheet

```bash
knowai memory list                                # all entries
knowai memory recall "OTP policy"                 # fuzzy search
knowai memory decide payment "Use idempotency" --body "..."
knowai memory forget <entry-id>
```

Dashboard URLs: `/entries` · `/syntheses` · `/audit` · `/healthz`

---

## Stop / wipe

```bash
docker compose stop                # keep data
docker compose down -v             # wipe all data
docker compose pull web && docker compose up -d   # upgrade
```

---

## Troubleshooting

| Problem                      | Fix                                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------ |
| `docker compose up` fails    | Docker Desktop not running                                                                             |
| `knowai: command not found`  | Open a new terminal (uv PATH not loaded)                                                               |
| AI doesn't call knowai tools | `knowai.config` missing or AI app started before MCP registered — restart it                           |
| Two entries not merging      | Bodies <0.92 cosine similarity. Reword closer, or check `docker compose logs web` for embedding errors |
| Port already in use          | Change `POSTGRES_PORT` / `WEB_PORT` in `.env`                                                          |

---

## Build from source

```bash
git clone https://github.com/qorstack/knowai.git && cd knowai
cp .env.example .env
docker compose up -d --build
uv sync --extra dev --extra postgres
uv run pytest
```

---

MIT — see [LICENSE](LICENSE).
