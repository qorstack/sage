# 11 — Tech Stack

## Backend (current)

| Layer | Stack | Reason |
|---|---|---|
| CLI | Typer | Modern, type-safe, great DX |
| API | FastAPI | Standard, fast, automatic OpenAPI |
| MCP | FastMCP (>=0.4.0) | Standard for Anthropic ecosystem |
| Graph | NetworkX | Pure Python, no extra infra |
| Memory (default) | JSON file | Zero deps |
| Memory (optional) | Qdrant + sentence-transformers | Semantic search |
| Config | Pydantic Settings | Type-safe env vars |
| Package | uv | Fast, modern Python tooling |
| Lint | ruff | Fast |
| Test | pytest | Standard |

## Parsing (current → planned)

| Now | Planned |
|---|---|
| Python `ast` + regex + ripgrep | **Tree-sitter** (accurate AST for all langs) |

Tree-sitter จะให้:
- Accurate function/class extraction
- Cross-language uniform API
- Faster than custom regex

## Frontend (Phase 4 — planned)

| Layer | Stack |
|---|---|
| Framework | Next.js 15 (app router) |
| UI | shadcn/ui + Tailwind v4 |
| Graph visualization | React Flow |
| State | Zustand |
| Charts | Recharts |
| Forms | react-hook-form + zod |
| Animation | Framer Motion |

## AI Layer (optional integrations)

| Purpose | Stack |
|---|---|
| Local models | Ollama (Qwen3, DeepSeek R1) |
| Cloud reasoning | OpenRouter (Claude, GPT, Gemini) |
| Embedding | sentence-transformers (all-MiniLM-L6-v2) |

**Note:** Reasoning engine core ไม่พึ่ง LLM — LLM ใช้แค่ optional augmentation (eg. auto-extract memory from PR description)

## Infra (production deployment)

| Service | Tool |
|---|---|
| API host | Fly.io / Railway / self-host docker |
| Postgres | Supabase / RDS |
| Vector DB | Qdrant Cloud / self-host |
| Queue | Redis / SQS (สำหรับ async memory extraction) |
| CI | GitHub Actions |
| Publish | PyPI (`uv publish`) |

## Dependencies summary

```toml
# pyproject.toml essentials
dependencies = [
    "typer>=0.12",
    "fastapi>=0.110",
    "fastmcp>=0.4",
    "networkx>=3",
    "pydantic>=2",
    "pydantic-settings>=2",
    "rich>=13",
    "toml>=0.10",
]

[project.optional-dependencies]
vector = [
    "qdrant-client>=1.7",
    "sentence-transformers>=2.5",
]
api = [
    "uvicorn[standard]>=0.27",
]
```

## Real-world usage (deployment)

```bash
# Solo dev → local file memory, no infra
uv add knowlyx
knowlyx mcp --repo .

# Small team → file memory + shared via git
# .knowlyx/memory.json checked into git
uv add knowlyx

# Larger team → Qdrant + Postgres + shared API
uv add "knowlyx[vector,api]"
docker compose up -d qdrant postgres
uvicorn knowlyx.api.main:app --host 0.0.0.0
```
