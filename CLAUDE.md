# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Knowlyx Is

Knowlyx is a **cognitive enforcement layer for AI software development** — not an AI coding assistant. Its purpose is to force AI agents to *understand* a software system (business logic, architecture, UX patterns, reusable assets, impact) *before* generating or modifying code.

Core thesis: **Knowledge is passive. Cognition must be enforced.**

## Development Commands

```bash
# Install (requires uv)
uv sync

# Run CLI
uv run knowlyx --help
uv run knowlyx scan /path/to/repo
uv run knowlyx analyze "add OTP login" --repo /path/to/repo
uv run knowlyx impact "fix payment scan 501" --repo /path/to/repo
uv run knowlyx conventions /path/to/repo
uv run knowlyx assets payment --repo /path/to/repo

# Start MCP server (stdio — for Claude Code integration)
uv run knowlyx mcp --repo /path/to/repo

# Start MCP server (SSE — for HTTP clients)
uv run knowlyx mcp --sse --port 8765 --repo /path/to/repo

# Start REST API
uv run uvicorn knowlyx.api.main:app --reload --port 8000

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_reasoning.py::test_risk_critical_delete -v

# Lint
uv run ruff check src/
uv run ruff format src/
```

## Architecture

Six layers, each in its own package under `src/knowlyx/`:

| Layer | Package | Responsibility |
| --- | --- | --- |
| Scanner | `scanner/` | Reads repo, infers language/framework/architecture, detects conventions and assets |
| Cognitive Graph | `graph/` | NetworkX DiGraph of domains, assets, conventions, and impact edges |
| Reasoning | `reasoning/` | Intent → Impact → Risk → Decision pipeline (rule-based, no LLM needed) |
| MCP Server | `mcp/` | FastMCP tools that AI agents must call before touching code |
| CLI | `cli/` | Typer CLI wrapping all cognitive commands |
| REST API | `api/` | FastAPI mirror of MCP tools for HTTP clients |

### Core data flow

```text
User request (string)
  → IntentAnalyzer     → IntentAnalysis   (domain, action, inferred requirements)
  → ImpactAnalyzer     → ImpactAnalysis   (affected domains, services, files, cascade risks)
  → RiskScorer         → RiskAssessment   (level, decision: proceed/warn/ask/reject)
  → ReasoningEngine    → CognitionReport  (full report with plan and reusable assets)
```

### MCP Tools (the enforcement surface)

All tools live in `src/knowlyx/mcp/server.py`. AI agents call these via MCP before coding:

- `analyze_intent(request, repo_path)` — **call first**, returns full CognitionReport
- `get_conventions(repo_path)` — detected rules AI must follow
- `get_reusable_assets(domain, repo_path)` — existing assets to reuse before creating new code
- `get_impact_analysis(change_description, repo_path)` — blast radius of a change
- `get_risk_analysis(request, repo_path)` — risk level + decision
- `get_project_context(repo_path)` — lightweight session orientation
- `refresh_scan(repo_path)` — bust the scan cache

### Claude Code MCP configuration

Add to `.claude/settings.json` in any target repo:

```json
{
  "mcpServers": {
    "knowlyx": {
      "command": "uv",
      "args": ["run", "knowlyx", "mcp", "--repo", "."],
      "cwd": "/path/to/knowlyx"
    }
  }
}
```

## Key Design Rules

- **MCP-first, not markdown-first** — Claude ignores markdown files. All cognition is delivered as structured tool results that Claude *must* query.
- **No LLM calls in the reasoning engine** — all reasoning is rule-based. Claude (via MCP) does the higher-level synthesis.
- **Scan cache** — `_state` dict in both `mcp/server.py` and `api/main.py` caches per `repo_path`. Call `refresh_scan` after structural changes.
- **Risk decisions are binding** — `reject` means stop; `ask` means pause for human confirmation. Never auto-proceed past these.
- **Multi-repo aware** — `repo_path` is always explicit; tools can target any repo, not just the one Knowlyx lives in.

## Planned Stack (not yet built)

- Vector memory: Qdrant (`qdrant-client` in deps, `memory/` package stubbed)
- Frontend: Next.js + shadcn/ui + React Flow (Phase 3)
- Local LLMs: Ollama (Phase 4)
