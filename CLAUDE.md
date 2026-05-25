# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Knowai Is

Knowai is a **cognitive enforcement layer for AI software development** — not an AI coding assistant. Its purpose is to force AI agents to *understand* a software system (business logic, architecture, UX patterns, reusable assets, impact) *before* generating or modifying code.

Core thesis: **Knowledge is passive. Cognition must be enforced.**

## Development Commands

```bash
# Install (requires uv)
uv sync

# Run CLI
uv run knowai --help
uv run knowai scan /path/to/repo
uv run knowai analyze "add OTP login" --repo /path/to/repo
uv run knowai impact "fix payment scan 501" --repo /path/to/repo
uv run knowai conventions /path/to/repo
uv run knowai assets payment --repo /path/to/repo
uv run knowai pack payment          # show built-in cognition pack

# Memory commands
uv run knowai memory list --repo /path/to/repo
uv run knowai memory recall "OTP policy" --repo /path/to/repo
uv run knowai memory decide payment "Use idempotency keys" --body "All payment calls require idempotency key" --repo /path/to/repo
uv run knowai memory forget <entry-id> --repo /path/to/repo

# Start MCP server (stdio — for Claude Code integration)
uv run knowai mcp --repo /path/to/repo

# Start MCP server (SSE — for HTTP clients)
uv run knowai mcp --sse --port 8765 --repo /path/to/repo

# Start REST API
uv run uvicorn knowai.api.main:app --reload --port 8000

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_memory.py::test_persistence -v

# Lint
uv run ruff check src/
uv run ruff format src/

# Build for PyPI
uv build
uv publish   # requires PYPI_TOKEN
```

## Architecture

Six layers, each in its own package under `src/knowai/`:

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

All tools live in `src/knowai/mcp/server.py`. AI agents call these via MCP before coding:

#### Phase 1 — Cognitive analysis

- `analyze_intent(request, repo_path)` — **call first**, full CognitionReport + packs + memory
- `get_conventions(repo_path)` — detected rules AI must follow
- `get_reusable_assets(domain, repo_path)` — existing assets to reuse before creating new code
- `get_impact_analysis(change_description, repo_path)` — blast radius of a change
- `get_risk_analysis(request, repo_path)` — risk level + proceed/warn/ask/reject decision
- `get_project_context(repo_path)` — lightweight session orientation
- `get_cognition_pack(domain)` — built-in domain knowledge (auth/otp/payment/webhook/order/notification/worker)
- `refresh_scan(repo_path)` — bust the scan cache

#### Phase 2 — Memory + Human approval

- `remember_business_context(domain, title, body, repo_path)` — save business knowledge (requires approval)
- `approve_memory(entry_id, approved_by, repo_path)` — human approves a memory as trusted
- `recall_context(query, domain, repo_path)` — fuzzy search approved memories
- `remember_team_decision(domain, title, decision, reason, repo_path)` — save + auto-approve team decisions
- `list_memory(domain, repo_path)` — list all memory entries
- `forget_memory(entry_id, repo_path)` — delete a memory entry

### Claude Code MCP configuration

Add to `.claude/settings.json` in any target repo:

```json
{
  "mcpServers": {
    "knowai": {
      "command": "uv",
      "args": ["run", "knowai", "mcp", "--repo", "."],
      "cwd": "/path/to/knowai"
    }
  }
}
```

## Key Design Rules

- **MCP-first, not markdown-first** — Claude ignores markdown files. All cognition is delivered as structured tool results that Claude *must* query.
- **No LLM calls in the reasoning engine** — all reasoning is rule-based. Claude (via MCP) does the higher-level synthesis.
- **Scan cache** — `_state` dict in both `mcp/server.py` and `api/main.py` caches per `repo_path`. Call `refresh_scan` after structural changes.
- **Risk decisions are binding** — `reject` means stop; `ask` means pause for human confirmation. Never auto-proceed past these.
- **Multi-repo aware** — `repo_path` is always explicit; tools can target any repo, not just the one Knowai lives in.

### Phase 3 — Workspace + Graph export + Approval queue

- `get_workspace_context(workspace_path)` — full multi-repo overview from knowai.toml
- `get_cross_repo_impact(changed_repo, change_description, workspace_path)` — cross-repo blast radius
- `export_graph(format, repo_path, workspace_path)` — react_flow | mermaid | dot
- `request_approval(title, description, risk_level, domain, ...)` — submit approval gate
- `check_approval(request_id)` — poll outcome (pending/approved/rejected)
- `approve_request(request_id)` / `reject_request(request_id, reason)` — human tools
- `list_approvals(status_filter)` — list approval queue

### Workspace (multi-repo)

Defined in `src/knowai/workspace/`. Driven by `knowai.toml` at workspace root:

```toml
name = "my-product"

[[repos]]
name = "api"
path = "./api"
role = "backend"
domains = ["payment", "auth"]
critical = true

[[repos]]
name = "web"
path = "./web"
role = "frontend"

[[dependencies]]
from = "web"
to = "api"
type = "api"
```

CLI: `knowai workspace init | scan | impact <repo> -c "..." | graph [mermaid|dot|react_flow]`

### Graph export

`src/knowai/graph/exporter.py` — `GraphExporter` produces:

- **React Flow JSON** — drop-in for `<ReactFlow nodes={} edges={} />` (Phase 3 frontend)
- **Mermaid** — paste into any markdown
- **DOT** — render with Graphviz

### Approval queue

`src/knowai/approval/queue.py` — stored in `.knowai/approvals.json`.

Flow: AI calls `request_approval()` → stores as `pending` → human runs `knowai approval approve <id>` → AI polls `check_approval()` → proceeds only on `approved`.

CLI: `knowai approval list | show <id> | approve <id> | reject <id> --reason "..."`

## Planned (Phase 4)

- AI self-review before submitting code
- Risk scoring ML model
- Architectural enforcement hooks
- Design cognition (UX/UI pattern detection)
- Local LLMs via Ollama

---

## Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

**Simplicity first.** Minimum code that solves the problem — no speculative features, no abstractions for single-use code.

**Surgical changes.** Touch only what's needed. Don't improve adjacent code. Match existing style.

**Surface tradeoffs.** If multiple interpretations exist, present them. If something is unclear, ask before implementing.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
