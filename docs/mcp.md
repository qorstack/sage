# 08 — MCP Integration (Enforcement Layer)

📂 [src/knowai/mcp/](../src/knowai/mcp/)

**The enforcement surface** — ทำให้ AI agents *ต้อง* query cognition ก่อน code

## ทำไม MCP-first ไม่ใช่ markdown-first

**ปัญหา:** Claude/Codex/Cursor *ignore* markdown files บ่อย — แม้จะใส่ใน CLAUDE.md / .cursorrules / AGENTS.md ก็ตาม

**Solution:** ทำเป็น **tool** — AI ตอบ tool result ได้ดีกว่าและเชื่อถือกว่า file content

```text
❌ AI → grep CLAUDE.md → maybe read maybe skip → maybe follow
✅ AI → MCP tool → structured result → trust → follow
```

## Setup

### Claude Code

```json
// .claude/settings.json
{
  "mcpServers": {
    "knowai": {
      "command": "uvx",
      "args": ["knowai", "mcp", "--repo", "."]
    }
  }
}
```

### Local dev (ก่อน publish PyPI)

```json
{
  "mcpServers": {
    "knowai": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/knowai", "knowai", "mcp", "--repo", "."]
    }
  }
}
```

### HTTP/SSE (สำหรับ web client)

```bash
uv run knowai mcp --sse --port 8765 --repo /path/to/repo
```

## 20 MCP Tools (Phase 1-3 ครบ)

### Phase 1 — Cognitive Analysis (8)

| Tool | use |
| --- | --- |
| `analyze_intent(request, repo_path)` | **call first** — full CognitionReport |
| `get_conventions(repo_path)` | rules AI ต้องตาม |
| `get_reusable_assets(domain, repo_path)` | assets ที่มีอยู่ |
| `get_impact_analysis(change, repo_path)` | blast radius |
| `get_risk_analysis(request, repo_path)` | risk level + decision |
| `get_project_context(repo_path)` | session orientation |
| `get_cognition_pack(domain)` | built-in domain knowledge |
| `refresh_scan(repo_path)` | bust cache |

### Phase 2 — Memory + Approval (6)

| Tool | use |
| --- | --- |
| `remember_business_context(domain, title, body, repo_path)` | AI propose memory (need approve) |
| `approve_memory(entry_id, approved_by, repo_path)` | human approves |
| `recall_context(query, domain, repo_path)` | fuzzy search approved memory |
| `remember_team_decision(domain, title, decision, reason, repo_path)` | auto-approved decision |
| `list_memory(domain, repo_path)` | list all |
| `forget_memory(entry_id, repo_path)` | delete |

### Phase 3 — Workspace + Graph + Approval Queue (8)

| Tool | use |
| --- | --- |
| `get_workspace_context(workspace_path)` | multi-repo overview |
| `get_cross_repo_impact(changed_repo, change, workspace_path)` | cross-repo blast radius |
| `export_graph(format, repo_path, workspace_path)` | react_flow/mermaid/dot |
| `request_approval(title, description, risk_level, domain, ...)` | submit approval gate |
| `check_approval(request_id)` | poll outcome |
| `approve_request(request_id)` | human approve |
| `reject_request(request_id, reason)` | human reject |
| `list_approvals(status_filter)` | queue list |

## Recommended AI workflow (บอก AI ใส่ใน prompt)

```text
For EVERY user request that touches code:

1. Call analyze_intent(user_request, repo_path) FIRST
2. Read CognitionReport:
   - If decision == "reject" → explain to user, propose alternative
   - If decision == "ask" → call request_approval(), poll check_approval()
   - If decision == "warn" → proceed but surface warnings
   - If decision == "proceed" → continue
3. Before creating new code, call get_reusable_assets(domain) → reuse if exists
4. Follow rules from get_conventions()
5. Apply cognition pack from result.packs
6. Inject relevant memory from result.memory (already filtered to approved)
```

## Real-world usage

**Scenario:** Dev ใน Claude Code พิมพ์ "add refund endpoint"

```text
[Claude]
1. tool: analyze_intent("add refund endpoint", "/path/to/api")
   ← decision: ASK (HIGH risk — billing domain + DB write)
   ← packs: billing (idempotency required, audit log, amount validation)
   ← memory: "refunds over $1000 require finance approval" (team_decision)
   ← assets: BillingService.charge() exists, refund() stub in src/billing/service.py

2. tool: request_approval(
     title="Add refund endpoint",
     description="POST /charges/{id}/refund — needs DB + finance flow",
     risk_level="HIGH",
     domain="billing"
   )
   ← request_id: abc-123

[Claude tells user]
"⚠️ Risk: HIGH — billing domain + DB change + finance approval flow.
Submitted approval request abc-123. Run `knowai approval show abc-123`
and approve before I write the code."

[User runs]
$ knowai approval approve abc-123

[Claude]
3. tool: check_approval("abc-123") → approved
4. Writes code reusing BillingService.refund() stub with idempotency key,
   audit log, finance check >$1000
```

→ Zero "AI ทำมั่ว" risk
