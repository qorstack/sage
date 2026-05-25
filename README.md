# knowai

**Cognitive enforcement layer for AI software development.**

> Knowledge is passive. Cognition must be enforced.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What is knowai

AI coding tools generate code fast — but they don't understand your system. They duplicate utilities, ignore conventions, miss cross-service impact, and re-invent decisions your team already made.

knowai sits between your AI assistant and your codebase. When you ask Claude *"add a refund endpoint"*, knowai intercepts and returns:

```text
Domain:    payment (HIGH)
Decision:  WARN — follow team conventions

Reuse:     PaymentClient, IdempotencyMiddleware
Memory:    "Use idempotency keys for all payment calls" (alice, approved)

Risk:      Touches 3 services. Cascade: refund → webhook → ledger
```

Claude reads this through MCP — it can't skip it. Result: code that follows team rules on the first try.

Knowledge is stored in **Postgres** with semantic auto-merge (similar entries merge into one). A web dashboard lets the team add/approve/audit knowledge without touching the DB.

---

## Prerequisites

| Need | Why |
|---|---|
| **Docker + Docker Compose v2** | run Postgres + dashboard |
| **Python 3.11+** with `uv` or `pipx` | *only* if you want AI/MCP integration (Part 2) |
| **~2GB RAM free** | embedding model loads in the web container |

Verify:

```bash
docker --version
docker compose version
```

---

## Part 1 — Dashboard (no clone, no Python)

### Step 1 — Make a folder and two files

```bash
mkdir knowai && cd knowai
```

Create **`.env`** with this content (defaults work for local use; for a team change `POSTGRES_PASSWORD`):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=knowai
POSTGRES_PASSWORD=knowai
POSTGRES_DB=knowai
POSTGRES_SCHEMA=public

WEB_PORT=8080
```

Create **`docker-compose.yml`** with this content:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: knowai-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-knowai}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-knowai}
      POSTGRES_DB: ${POSTGRES_DB:-knowai}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - knowai_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-knowai} -d ${POSTGRES_DB:-knowai}"]
      interval: 5s
      timeout: 3s
      retries: 10

  web:
    image: qorstack/knowai:latest
    container_name: knowai-web
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-knowai}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-knowai}
      POSTGRES_DB: ${POSTGRES_DB:-knowai}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_SCHEMA: ${POSTGRES_SCHEMA:-public}
    ports:
      - "${WEB_PORT:-8080}:8080"

volumes:
  knowai_pgdata:
```

### Step 2 — Start the stack

```bash
docker compose up -d
```

First run pulls the images (~30s). Then both services come up:

- **`knowai-postgres`** on port `5432` — stores knowledge (schema auto-bootstraps)
- **`knowai-web`** on port `8080` — team dashboard

Wait until both are healthy:

```bash
docker compose ps
```

Both rows should show `Up X seconds (healthy)`.

### Step 3 — Open the dashboard

Open <http://localhost:8080> in your browser.

You'll see the **Overview** page with all counts at 0.

### Step 4 — Add your first knowledge entry

1. Click **Knowledge** in the top nav, then **+ Add new**.
2. Fill in two things:
   - **Title** — `Use idempotency keys`
   - **Content** — `All POST /payments require an Idempotency-Key header.`
     (Plain markdown — toolbar gives you bold/italic/headings/code/lists; **Preview** tab renders it.)
3. *(Optional)* tick **Mark as approved** if your team has already signed off.
4. Click **Save** → you land on the entry detail page.

Go back to **Home** — `Knowledge items = 1`, `Approved = 1`.

**On any entry detail page** you can:

- **Edit** — change title/content (logged as `update`)
- **Approve** — flip status if pending (logged as `approve`)
- **Delete** — remove the entry (kept in audit log)

> **Note on defaults.** The web form keeps things simple — every new entry gets `domain = general`, `kind = team_decision`, and no tags. If you want a different domain/kind/tags (used for grouping and AI-tool queries), set them via the CLI: `knowai memory decide <domain> "<title>" --body "..." --tags a,b,c`.

✅ If you only need a team knowledge base, **you're done**. Skip to [Manage / inspect](#manage--inspect) or [Stop / restart](#stop--restart--wipe).

---

## Part 2 — AI integration (optional)

This part connects the dashboard's Postgres to Claude Code / Cursor / any MCP client via a CLI.

### Step 5 — Install the CLI

Pick **one** (uv recommended):

```bash
# uv (recommended)
uv tool install git+https://github.com/qorstack/knowai.git

# or pipx
pipx install git+https://github.com/qorstack/knowai.git
```

Verify it's on your PATH:

```bash
knowai --version
```

If `command not found`, open a new terminal (uv/pipx adds to your PATH on first install).

### Step 6 — Give the CLI your credentials

Drop one file in your home directory:

```bash
cat > ~/.knowai.config <<'EOF'
[database]
host     = "localhost"
port     = 5432
user     = "knowai"
password = "knowai"
db       = "knowai"
schema   = "public"
EOF
```

Verify:

```bash
knowai memory list   # prints [] or your entries — no error
```

### Step 6½ — Identify each repo to a workspace

For every repo that should join a workspace, drop a `./knowai.config` at its root:

```toml
workspace = "my-product"
repo_name = "aaa-api"
role      = "backend"        # optional
domains   = ["payment"]      # optional
```

`repo_name` is **explicit on purpose** — folder names get renamed, the identity shouldn't. Commit `./knowai.config` to git so every dev who clones the repo is auto-connected to the same workspace.

- Generate it with `knowai link my-product --name aaa-api --role backend`, or write it by hand. See [`knowai.config.example`](knowai.config.example).
- A repo can also carry its own `[database]` section here to override `~/.knowai.config`.
- Repos without `./knowai.config` simply aren't linked — knowai falls back to a per-repo local store. A dev who hasn't installed knowai is unaffected; the file is ignored.

**Config precedence** (highest first): process env → `./knowai.config` (cwd or any parent) → `~/.knowai.config` → `.env`.

### Step 6¾ — (optional) Seed knowledge from an existing repo

For repos you've already built, `knowai generate` scans the code and produces a starting set of memory entries (overview, conventions, reusable assets, risk patterns):

```bash
cd ~/code/aaa-api
knowai generate                     # dry-run — preview proposed entries
knowai generate --save              # persist as pending (review in dashboard)
knowai generate --save --approve    # persist + auto-approve (use when you trust the scan)
```

Then refine them in the dashboard — edit titles, delete noise, approve the keepers.

### Step 7 — Connect to Claude Code

Register knowai **once at user scope** so it works in every project — no need to re-register per repo:

```bash
claude mcp add --scope user knowai -- knowai mcp
claude mcp list      # should show: knowai ✓
```

After this, **every chat with Claude in any folder** automatically queries knowai before generating code.

> Drop the `--scope user` if you want knowai available in **this project only** (the default `local` scope).

#### Or Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "knowai": {
      "command": "knowai",
      "args": ["mcp"]
    }
  }
}
```

Restart Cursor.

### Step 8 — Confirm the AI uses it

In your AI chat, type:

> "Add a refund endpoint to /payments"

**How to know it worked:**

- **Claude Code**: you'll see a `knowai` tool call indicator in the response.
- **Cursor**: hover the assistant message — MCP tool calls appear inline.
- The reply mentions your Step 4 entry about idempotency keys.

If you see no MCP call:

- Confirm registration: `claude mcp list` should show `knowai ✓`. If it shows `✗`, run `knowai mcp` manually in a terminal — the error tells you what's missing (usually credentials).
- Make sure `~/.knowai.config` exists (Step 6), or that the repo you ran Claude in has its own `knowai.config`.

---

## Verify auto-merge

Add a **second** entry with similar wording (web form defaults both entries to `domain = general`, which is what auto-merge keys on):

- **Title**: `Idempotency-Key header is mandatory for payment endpoints`
- **Content**: `All POST /payments require an Idempotency-Key header to safely retry. Keys kept 24h.`

After submit you should land on the **original entry** (same id), not a new one. Check:

- "This item absorbed 1 similar submission(s)" appears under **Merge history**
- A `contributors` row lists the second entry's original title
- Content has the new text appended after a `---` separator
- **History** section shows `insert` + `merge` rows
- Home still shows `Knowledge items = 1` (not 2)

**If you see 2 separate entries:**

| Cause | Fix |
|---|---|
| Bodies aren't similar enough (cosine < 0.92) | Use wording closer to the first entry. The threshold is intentionally strict to avoid wrong merges. |
| Embedding model failed to load in the container | `docker compose logs web` — look for `sentence-transformers` errors. Restart `web` after first-run download finishes. |

---

## Manage / inspect

### From the dashboard

| URL | What it shows |
|---|---|
| <http://localhost:8080> | **Home** — counts + recent activity |
| <http://localhost:8080/entries> | **Knowledge** — list of items, search/filter, edit/approve/delete |
| <http://localhost:8080/entries?add=true> | **Add knowledge** — full-page editor (Title + markdown content) |
| <http://localhost:8080/entries/{id}> | Item detail with Edit / Approve / Delete + history |
| <http://localhost:8080/syntheses> | **Summaries** — per-domain AI summaries + drift detection |
| <http://localhost:8080/audit> | **Activity** — full audit log, filter by action |
| <http://localhost:8080/healthz> | JSON status (for monitoring) |

### From psql (no password needed via `docker exec`)

```bash
docker exec knowai-postgres psql -U knowai -d knowai -c "\dt"
# → memory_entries, memory_entry_embeddings, memory_syntheses, memory_audit_log

docker exec knowai-postgres psql -U knowai -d knowai \
  -c "SELECT id, title, (metadata->>'merge_count')::int AS merges FROM memory_entries;"
```

---

## Stop / restart / wipe

```bash
docker compose stop          # stop, keep data
docker compose start         # start again
docker compose down          # remove containers (data kept in volume)
docker compose down -v       # also wipe all data
```

To upgrade to a new web image:

```bash
docker compose pull web && docker compose up -d
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `docker compose up` fails | Make sure Docker Desktop is running |
| Web shows `unhealthy` for >30s | Postgres still booting first time. Check `docker compose logs web` |
| Port `5432` / `8080` already in use | Change `POSTGRES_PORT` / `WEB_PORT` in `.env`, then `docker compose up -d` |
| `knowai: command not found` | Open a new terminal (uv/pipx PATH not loaded yet) |
| AI doesn't call knowai tools | `~/.knowai.config` missing/misconfigured, OR Claude/Cursor started before you created it — restart the AI app and check `claude mcp list` shows `knowai ✓` |
| Two similar entries instead of one merged | See [Verify auto-merge](#verify-auto-merge) outcomes table above |
| Embedding model OOM on first start | Container needs ~2GB free RAM. Close other apps and `docker compose restart web` |
| `docker pull qorstack/knowai` fails | Image not published yet — wait for `Publish Docker image` workflow to finish. Or build locally via the [Build from source](#build-from-source-contributors) section |

---

## Build from source (contributors)

```bash
git clone https://github.com/qorstack/knowai.git
cd knowai
cp .env.example .env
docker compose up -d --build      # uses the local Dockerfile instead of the published image
uv sync --extra dev --extra postgres
uv run pytest
```

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
