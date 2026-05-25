# 03 — Architecture Overview

6 layers, package เดียวต่อ layer

```text
┌─────────────────────────────────────────────────┐
│  AI Agent (Claude / Codex / Cursor / Cline)     │
└──────────────────┬──────────────────────────────┘
                   │ MCP protocol
┌──────────────────▼──────────────────────────────┐
│  Layer 6: ENFORCEMENT (mcp/server.py)           │
│  20 MCP tools — AI ต้อง call ก่อนเขียน code     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Layer 5: REASONING (reasoning/)                │
│  Intent → Impact → Risk → Decision              │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Layer 2  │ │ Layer 3  │ │ Layer 4  │
│ GRAPH    │ │ MEMORY   │ │ PACKS    │
│ graph/   │ │ memory/  │ │ packs/   │
└────┬─────┘ └──────────┘ └──────────┘
     │
┌────▼────────────────────────────────────────────┐
│  Layer 1: SCANNER (scanner/)                    │
│  อ่าน repo → infer stack/architecture/assets    │
└─────────────────────────────────────────────────┘
```

## Layers

| # | Layer | Package | Responsibility | Status |
| --- | --- | --- | --- | --- |
| 1 | **Scanner** | [scanner/](../src/knowai/scanner/) | อ่าน repo, infer language/framework/architecture/conventions/assets | ✅ |
| 2 | **Cognitive Graph** | [graph/](../src/knowai/graph/) | NetworkX DiGraph + cascade rules + exporter | ✅ |
| 3 | **Memory** | [memory/](../src/knowai/memory/) | FileStore + Qdrant fallback + human approval | ✅ |
| 4 | **Cognition Packs** | [packs/](../src/knowai/packs/) | Built-in domain knowledge | ✅ |
| 5 | **Reasoning** | [reasoning/](../src/knowai/reasoning/) | Intent/Impact/Risk analyzers + engine | ✅ |
| 6 | **Enforcement** | [mcp/](../src/knowai/mcp/) | FastMCP server, 20 tools | ✅ |

Surfaces ที่ exposing layer เหล่านี้:

- [cli/](../src/knowai/cli/) — Typer CLI (ทุก command)
- [api/](../src/knowai/api/) — FastAPI REST (Phase 1 routes only — Phase 2-3 ยังขาด)
- [workspace/](../src/knowai/workspace/) — Multi-repo orchestrator
- [approval/](../src/knowai/approval/) — Human approval queue

## Core data flow

```text
User: "add rate limiting to /login endpoint"
  │
  ▼
IntentAnalyzer       → IntentAnalysis(domain=auth, action=add, requirements=[...])
  │
  ▼
ImpactAnalyzer       → ImpactAnalysis(domains=[auth,audit], files=[...], cascade_risks=[...])
  │
  ▼
RiskScorer           → RiskAssessment(level=MEDIUM, decision=WARN)
  │
  ▼
ReasoningEngine      → CognitionReport(intent, impact, risk, plan, reusable_assets, conventions, packs, memory)
  │
  ▼ (via MCP tool result)
AI Agent             → reads report → writes code that respects constraints
```

## Design rules (binding)

1. **MCP-first, not markdown-first** — Claude ignore markdown, trust tool result
2. **No LLM calls in reasoning engine** — rule-based, deterministic, fast, free
3. **Scan cache per repo_path** — `_state` dict; bust via `refresh_scan`
4. **Risk decisions binding** — `reject` = stop; `ask` = pause for human
5. **Multi-repo aware** — `repo_path` explicit ทุก tool, ไม่ assume CWD
6. **Human approves understanding** — AI propose, human approve memory/decisions

## Real-world usage

**ตัวอย่าง integration กับ Claude Code:**

```json
// .claude/settings.json ของ project ที่ต้องการ enforce
{
  "mcpServers": {
    "knowai": {
      "command": "uvx",
      "args": ["knowai", "mcp", "--repo", "."]
    }
  }
}
```

Claude Code launch → MCP handshake → Claude เห็น 20 tools ของ Knowai → ทุก request ของ user, Claude ต้อง call `analyze_intent` ก่อน
