# 12 — Roadmap

สถานะ ณ 2026-05-22

## ✅ Phase 1 — System Understanding (code complete)

- [x] Scanner: language/framework/architecture/domain detection
- [x] ConventionDetector
- [x] AssetDetector (reusable components/hooks/utils)
- [x] CognitiveGraph (NetworkX + cascade rules)
- [x] IntentAnalyzer
- [x] ImpactAnalyzer
- [x] RiskScorer
- [x] ReasoningEngine
- [x] 8 MCP tools (analyze_intent, get_conventions, ...)
- [x] CLI (scan, analyze, impact, conventions, assets)
- [x] REST API (Phase 1 routes)
- [ ] ⚠️ **tests ยังไม่ได้ run** — เขียนแล้วยังไม่ verify

## ✅ Phase 2 — Memory + Cognition Packs (code complete)

- [x] FileMemoryStore
- [x] QdrantMemoryStore + fallback
- [x] Human approval workflow
- [x] Memory types (business_context, team_decision, ...)
- [x] 7 Cognition Packs (auth/otp/payment/webhook/order/notification/worker)
- [x] 6 MCP tools (memory + packs)
- [x] CLI (memory list/recall/decide/forget, pack)
- [x] PyPI ready (`__main__.py`, classifiers, README)

## ✅ Phase 3 — Workspace + Graph + Approval (code complete)

- [x] `knowlyx.toml` config
- [x] WorkspaceScanner (parallel scan)
- [x] Inferred dependencies (frontend/worker → backend)
- [x] CrossRepoImpactAnalyzer
- [x] GraphExporter (React Flow / Mermaid / DOT)
- [x] ApprovalQueue
- [x] 8 MCP tools
- [x] CLI (workspace, approval, graph)

## 🔴 Critical blockers — ก่อน ship จริง

| Task | Why |
|---|---|
| `uv sync` + `uv run pytest` | ไม่รู้ว่า deps conflict หรือ tests pass |
| Verify FastMCP API (`mcp.run(transport="stdio")`) | API อาจเปลี่ยน |
| Integration test กับ Claude Code จริง | proof ว่า MCP server work |
| REST API: เพิ่ม route Phase 2-3 | memory/workspace/approval ยังไม่มี endpoint |

## 🟡 ควรทำก่อน publish

| Task | Why |
|---|---|
| `knowlyx init` command | auto-gen `knowlyx.toml` |
| GitHub Actions CI | test + publish PyPI |
| Example workspace template | dev copy ใช้ได้ทันที |
| Error handling edge cases | permission denied, binary files, symlinks |
| API docs verify (`/docs`) | FastAPI auto-gen แต่ไม่เคย check |

## ✅ Phase 4.A — Distributed Knowledge (code complete)

- [x] `src/knowlyx/paths.py` — central path resolver + KNOWLYX_HOME env
- [x] `src/knowlyx/link/` — per-repo `.knowlyx/config.toml` + auto-resolver
- [x] Memory store auto-resolves central workspace (backward compatible)
- [x] Approval queue auto-resolves central workspace (backward compatible)
- [x] Workspace config_loader falls back to central path
- [x] CLI: `workspace create/list`, `link`, `unlink`, `migrate`
- [x] Tests: `test_paths.py`, `test_link.py`
- [ ] ⚠️ run `uv sync && pytest` to verify (environment doesn't have uv yet)

ดูรายละเอียดทั้งหมดที่ [15_DISTRIBUTED_KNOWLEDGE.md](15_DISTRIBUTED_KNOWLEDGE.md)

## 🔵 Phase 4.B — Workspace-aware analysis (not started)

- [ ] Persistent scan cache at `~/.knowlyx/workspaces/<name>/scans/<repo>.json`
- [ ] `WorkspaceScanner` reads cached scan when repo not on disk
- [ ] `ImpactAnalyzer` cross-repo answers work even with single clone
- [ ] CLI: `knowlyx workspace scan --all --persist` (for CI/tech lead)

## 🔵 Phase 4.C — Git sync (not started)

- [ ] `src/knowlyx/sync/git_sync.py` — pull/push central store to git remote
- [ ] CLI: `knowlyx sync init/pull/push/status`
- [ ] Conflict resolution: timestamp-based merge for memory.json

## 🔵 Phase 4 — Original (still planned)

### 4.1 AI Self-Review
AI ตรวจ code ของตัวเองก่อน submit
- new MCP tool: `validate_generated_code(code, repo_path)`
- check: conventions, reuse, design tokens, forbidden patterns
- return: violations + fix suggestions

### 4.2 Design Cognition (UX/UI)
ดู [10_UX_UI_COGNITION.md](10_UX_UI_COGNITION.md)

### 4.3 Architectural Enforcement Hooks
- pre-commit hook ที่ require AI to have called `analyze_intent`
- CI gate ที่ block PR ถ้า AI bypass cognition
- enforced via git trailer / commit metadata

### 4.4 Risk Scoring ML
- เปลี่ยนจาก rule-based เป็น model-based
- training data: historical incidents + PR review comments
- output: probability of incident per change

### 4.5 Local LLMs
- Ollama integration สำหรับ optional augmentation
- ex: auto-extract memory จาก PR description
- ex: summarize cognition report

### 4.6 Frontend UI (Next.js)
- Cognitive graph visualizer (React Flow)
- Memory browser + approval queue
- Workspace topology
- Approval inbox (HIGH/CRITICAL queue)

## 🟢 Future Vision (Phase 5+)

| Idea | Why interesting |
|---|---|
| **Business conflict detection** | feature ใหม่ขัด policy เก่า — ยังไม่มีใครทำดี |
| **Business evolution log** | track ว่า rule เปลี่ยนเมื่อไหร่/ทำไม |
| **Auto-extract from PRs** | parse PR description → propose memory entries |
| **WHY.md auto-generator** | document *why* ไม่ใช่ *what* |
| **Cross-team cognition sync** | share approved memory ข้าม org |
| **Slack/Linear integration** | discuss → auto-propose memory |

## Suggested next 3 sprints

| Sprint | Goal |
|---|---|
| Sprint 1 | Run tests, fix deps, integration test กับ Claude Code real |
| Sprint 2 | `knowlyx init`, complete REST API, CI/CD, publish PyPI |
| Sprint 3 | Phase 4.1 (AI self-review) + 4.3 (commit hooks) — สอง feature ที่ user เห็นค่าทันที |
