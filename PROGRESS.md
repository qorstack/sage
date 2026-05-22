# Knowlyx — Build Progress

> Cognitive enforcement layer for AI software development.
> **AI must understand the system before touching code.**

---

## Vision

แทนที่จะสร้าง Documentation Layer ที่ AI อาจไม่อ่าน —  
Knowlyx สร้าง **Decision Enforcement Layer** ที่บังคับ AI ผ่าน workflow การคิดก่อน generate code ทุกครั้ง

```
User Request
  → Intent Analysis      (domain, action, inferred requirements)
  → Impact Analysis      (affected domains, services, cascade risks)
  → Risk Scoring         (proceed / warn / ask / reject)
  → Cognition Pack       (built-in domain knowledge)
  → Memory Recall        (team-approved business context)
  → Human Approval       (กรณี HIGH/CRITICAL risk)
  → Plan Generation
  → Code Generation
```

---

## สถาปัตยกรรมทั้งหมด

```
src/knowlyx/
  scanner/        ← อ่าน repo → ตรวจ stack, architecture, domain, convention, assets
  graph/          ← NetworkX cognitive graph + exporter (React Flow / Mermaid / DOT)
  reasoning/      ← Intent → Impact → Risk → Decision pipeline (rule-based)
  memory/         ← Persistent memory (FileStore + Qdrant fallback)
  packs/          ← Built-in domain cognition packs (7 domains)
  approval/       ← Human approval queue
  workspace/      ← Multi-repo workspace (knowlyx.toml + cross-repo graph)
  mcp/            ← FastMCP server — 20 tools ที่ AI ต้อง call ก่อน code
  cli/            ← Typer CLI — ทุก command
  api/            ← FastAPI REST API (Phase 1 ครบ)
  models/         ← Pydantic schemas ทั้งหมด
  config.py       ← Settings (pydantic-settings)
```

---

## Phase 1 — System Understanding ✅ เสร็จแล้ว

> Goal: AI เข้าใจ system ก่อน code — โดยไม่ต้องให้คนอธิบายทุกครั้ง

### สิ่งที่ build

#### Scanner Layer (`src/knowlyx/scanner/`)

| ไฟล์ | หน้าที่ |
| --- | --- |
| `repo_scanner.py` | ตรวจ language, framework, architecture pattern, domains, API clients, forbidden patterns |
| `convention_detector.py` | ตรวจ naming conventions, import rules, architecture conventions, lint rules, test patterns |
| `asset_detector.py` | ตรวจ reusable components, hooks, utils, services พร้อม tag ตาม domain |

Architecture patterns ที่ตรวจได้: `clean_architecture`, `ddd`, `modular_monolith`, `layered`, `microservices`

Stacks ที่ตรวจได้: Python (FastAPI/Django/Flask), TypeScript/JS (Next.js/React/NestJS/Express), Go, Rust, Java

#### Cognitive Graph (`src/knowlyx/graph/`)

- `cognitive_graph.py` — NetworkX DiGraph
- Nodes: domain, component, hook, util, service, convention
- Edges: `belongs_to`, `impacts`, `enforced_by`
- Built-in cascade rules: payment → webhook/audit/notification/order, auth → user/audit/notification, order → payment/inventory/shipping ฯลฯ

#### Reasoning Layer (`src/knowlyx/reasoning/`)

| ไฟล์ | Input → Output |
| --- | --- |
| `intent_analyzer.py` | request (string) → `IntentAnalysis` (domain, action, inferred requirements, clarification questions) |
| `impact_analyzer.py` | `IntentAnalysis` → `ImpactAnalysis` (affected domains, services, files, cascade risks) |
| `risk_scorer.py` | intent + impact → `RiskAssessment` (level, decision, warnings, workflow) |
| `engine.py` | request → `CognitionReport` (ทั้งหมดรวมกัน) |

Risk decisions: `proceed` / `warn` / `ask` / `reject`

#### MCP Server — Phase 1 Tools

| Tool | หน้าที่ |
| --- | --- |
| `analyze_intent(request, repo_path)` | **เรียกก่อนเสมอ** — full cognitive report |
| `get_conventions(repo_path)` | rules ที่ AI ต้องทำตาม |
| `get_reusable_assets(domain, repo_path)` | assets ที่มีอยู่แล้ว ก่อนสร้างใหม่ |
| `get_impact_analysis(change, repo_path)` | blast radius ของ change |
| `get_risk_analysis(request, repo_path)` | risk level + decision |
| `get_project_context(repo_path)` | overview สำหรับ orient ตอนต้น session |
| `refresh_scan(repo_path)` | bust cache หลัง structural changes |

#### CLI — Phase 1 Commands

```bash
knowlyx scan /path/to/repo
knowlyx analyze "add OTP login" --repo /path/to/repo
knowlyx impact "fix payment scan 501" --repo /path/to/repo
knowlyx conventions /path/to/repo
knowlyx assets payment --repo /path/to/repo
```

#### REST API (`src/knowlyx/api/main.py`)

`POST /analyze` · `POST /scan` · `POST /conventions` · `POST /assets` · `POST /impact` · `POST /refresh` · `GET /health`

---

## Phase 2 — Memory + Cognition Packs ✅ เสร็จแล้ว

> Goal: AI จำ context ข้าม session ได้ และมี domain knowledge ที่ built-in

### สิ่งที่ build

#### Memory Layer (`src/knowlyx/memory/`)

**`FileMemoryStore`** — default, zero dependencies
- เก็บเป็น JSON ใน `.knowlyx/memory.json` ภายใน project
- search ด้วย keyword scoring
- persist ข้าม session

**`QdrantMemoryStore`** — optional, semantic search
- ใช้ `qdrant-client` + `sentence-transformers` (all-MiniLM-L6-v2)
- fallback ไป FileMemoryStore อัตโนมัติถ้าไม่มี Qdrant
- install ด้วย `uv sync --extra vector`

Memory types: `business_context`, `approved_convention`, `team_decision`, `reusable_asset`, `risk_pattern`, `workflow`

**Human approval principle**: AI save memory → `approved=False` → human call `approve_memory()` → trusted  
`analyze_intent` inject เฉพาะ approved memory เข้า report

#### Cognition Packs (`src/knowlyx/packs/`)

Built-in packs สำหรับ 7 domains — แต่ละ pack มี:
- `business_rules` — กฎที่ห้ามละเมิด
- `common_requirements` — สิ่งที่ต้อง implement ทุกครั้ง
- `risk_flags` — จุดอันตราย
- `required_workflow` — ลำดับขั้นตอน
- `forbidden_shortcuts` — shortcuts ที่ห้ามใช้
- `questions_to_ask` — ถามก่อน implement

| Domain | ตัวอย่าง business rule |
| --- | --- |
| `auth` | Passwords must never be stored in plain text, JWT must have expiration, rate limiting required |
| `otp` | OTP must expire (5–10 min), single-use, max retry before lock |
| `payment` | Idempotency key required, never trust client-side amount, webhook must verify signature |
| `webhook` | Respond 200 immediately → process async via queue, idempotency by event ID |
| `order` | State machine (no backward transitions), reserve stock before payment |
| `notification` | Always async, respect user preferences, retry on failure |
| `worker` | Jobs must be idempotent, max retry defined, DLQ required |

#### MCP Server — Phase 2 Tools

| Tool | หน้าที่ |
| --- | --- |
| `get_cognition_pack(domain)` | domain knowledge bundle |
| `remember_business_context(domain, title, body)` | save ความรู้ (ต้อง approve ก่อน trust) |
| `approve_memory(entry_id)` | human approve memory เป็น trusted |
| `recall_context(query, domain)` | fuzzy search approved memories |
| `remember_team_decision(domain, title, decision)` | save + auto-approve team decisions |
| `list_memory(domain)` | list all entries |
| `forget_memory(entry_id)` | delete entry |

#### CLI — Phase 2 Commands

```bash
knowlyx pack payment
knowlyx memory list --repo /path/to/repo
knowlyx memory recall "OTP expiry policy"
knowlyx memory decide payment "Use idempotency keys" --body "All payment calls require idempotency key"
knowlyx memory forget <entry-id>
```

#### PyPI Ready

- `src/knowlyx/__main__.py` → `uvx knowlyx mcp --repo .` ใช้ได้เลย
- `pyproject.toml` มี classifiers, URLs, optional deps
- `README.md` พร้อม one-liner install

**One-liner install สำหรับ Claude Code:**
```bash
claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

---

## Phase 3 — Workspace + Graph + Approval Queue ✅ เสร็จแล้ว

> Goal: Multi-repo awareness + human-in-the-loop approval + graph visualization data

### สิ่งที่ build

#### Workspace (`src/knowlyx/workspace/`)

**`knowlyx.toml`** — config file ที่กำหนด multi-repo workspace:

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

[[repos]]
name = "worker"
path = "./worker"
role = "worker"

[[dependencies]]
from = "web"
to = "api"
type = "api"

[[dependencies]]
from = "worker"
to = "api"
type = "event"
```

**`WorkspaceScanner`** — scan repos ทั้งหมดพร้อมกัน สร้าง cross-repo NetworkX graph

Inferred edges อัตโนมัติ:
- frontend ที่มี generated API client → backend
- worker repos ที่ share domain → source repos
- declared dependencies จาก `knowlyx.toml`

**`CrossRepoImpactAnalyzer`** — วิเคราะห์ blast radius ข้าม repo  
ตอบว่า: เมื่อ repo A เปลี่ยน → repo ไหนกระทบ, กี่ repo, มี critical repo อยู่ไหม

#### Graph Export (`src/knowlyx/graph/exporter.py`)

| Format | ใช้กับ |
| --- | --- |
| `react_flow` | `<ReactFlow nodes={} edges={} />` component โดยตรง — พร้อมสำหรับ Phase 3 UI |
| `mermaid` | paste ใน markdown, GitHub, Notion |
| `dot` | render ด้วย Graphviz (`dot -Tpng graph.dot > graph.png`) |

Export ได้ทั้ง single-repo cognitive graph และ cross-repo workspace graph

Node styling ตาม kind/role (domain=purple, backend=blue, frontend=violet, worker=orange, critical=shadow)

#### Approval Queue (`src/knowlyx/approval/queue.py`)

Flow สำหรับ HIGH/CRITICAL risk:

```
AI calls request_approval()
  → status: pending
  → Human: knowlyx approval approve <id>
  → AI calls check_approval()
  → status: approved → proceed
  → status: rejected → STOP, ask human
```

เก็บใน `.knowlyx/approvals.json` ภายใน project

#### MCP Server — Phase 3 Tools

| Tool | หน้าที่ |
| --- | --- |
| `get_workspace_context(workspace_path)` | overview ของทุก repo ใน workspace |
| `get_cross_repo_impact(changed_repo, change, workspace_path)` | cross-repo blast radius |
| `export_graph(format, repo_path, workspace_path)` | react_flow / mermaid / dot |
| `request_approval(title, description, risk_level, domain, ...)` | submit approval gate |
| `check_approval(request_id)` | poll outcome → pending / approved / rejected |
| `approve_request(request_id)` | human approves |
| `reject_request(request_id, reason)` | human rejects |
| `list_approvals(status_filter)` | list approval queue |

#### CLI — Phase 3 Commands

```bash
# Workspace
knowlyx workspace init
knowlyx workspace scan
knowlyx workspace impact api --change "fix payment DTO"
knowlyx workspace graph
knowlyx workspace graph react_flow --json

# Approval
knowlyx approval list
knowlyx approval show <id>
knowlyx approval approve <id>
knowlyx approval reject <id> --reason "too risky before release"

# Graph (single repo)
knowlyx graph mermaid --repo /path/to/repo
knowlyx graph dot --repo /path/to/repo
knowlyx graph react_flow --repo /path/to/repo
```

---

## Tests ที่เขียนแล้ว

| ไฟล์ | ครอบคลุม |
| --- | --- |
| `tests/test_scanner.py` | scan self, empty dir, Node.js project |
| `tests/test_reasoning.py` | intent detection, risk scoring, full report |
| `tests/test_memory.py` | save/get, search, filter unapproved, delete, persistence |
| `tests/test_packs.py` | all packs valid, get pack, unknown domain, deduplication |
| `tests/test_workspace.py` | config save/load, init, get_dependents, scan, cross-repo impact |
| `tests/test_approval.py` | submit, approve, reject, filter, persistence |
| `tests/test_graph_exporter.py` | React Flow, Mermaid, DOT format validation |

**⚠ ยังไม่ได้ run จริง** — `uv sync` ยังไม่ได้ทำ

---

## สิ่งที่ขาด / ยังไม่ได้ทำ

### 🔴 Critical — ต้องทำก่อน ship

| รายการ | ปัญหา |
| --- | --- |
| `uv sync` + run tests | ยังไม่รู้ว่า deps conflict หรือ tests pass ไหม |
| FastMCP API compatibility | `fastmcp>=0.4.0` — ต้องยืนยัน `mcp.run(transport="stdio")` API ตรงกัน |
| REST API Phase 2–3 | `api/main.py` มีแค่ Phase 1 routes — memory, workspace, approval ยังไม่อยู่ |
| Integration test with Claude | ยังไม่มีหลักฐานว่า MCP server ทำงานกับ Claude Code จริง |

### 🟡 ควรทำก่อน publish

| รายการ | ปัญหา |
| --- | --- |
| `knowlyx init` command | ยังไม่มี command ที่ auto-scan repo แล้วสร้าง `knowlyx.toml` ให้เลย |
| CI/CD Pipeline | ไม่มี `.github/workflows/` สำหรับ test + publish PyPI |
| `knowlyx.toml` example | ไม่มี template ให้ user copy |
| API docs | FastAPI `/docs` จะมีเอง แต่ยังไม่ได้ verify |
| Error handling | edge cases ใน scanner (permission denied, binary files, symlinks) |

### 🔵 Phase 4 — ยังไม่ได้เริ่ม

| Feature | คือ |
| --- | --- |
| AI self-review | AI ตรวจ code ของตัวเองก่อน submit — วิเคราะห์ว่าตรงกับ conventions ไหม |
| Design cognition | ตรวจ UX/UI patterns — spacing, component style, dark mode, modal flow |
| Architectural enforcement hooks | pre-commit hook / CI gate ที่ block commit ถ้า AI bypass cognition |
| Risk scoring ML | เปลี่ยนจาก rule-based เป็น model-based risk scoring |
| Local LLMs (Ollama) | รัน reasoning บน local model แทน rule-based |
| Frontend UI | Next.js + React Flow — visualize cognitive graph, approval queue, memory browser |

---

## Install & Quick Start

```bash
# Self-host
git clone https://github.com/SatangBudsai/knowlyx
cd knowlyx
uv sync
uv run knowlyx mcp --repo /path/to/your/project

# หรือผ่าน uvx (เมื่อ publish ขึ้น PyPI แล้ว)
claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

**Claude Code MCP config** (`.claude/settings.json` ใน project ที่ต้องการ enforce):
```json
{
  "mcpServers": {
    "knowlyx": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/knowlyx", "knowlyx", "mcp", "--repo", "."]
    }
  }
}
```

---

## MCP Tools ทั้งหมด (20 tools)

### Phase 1 — Cognitive Analysis
`analyze_intent` · `get_conventions` · `get_reusable_assets` · `get_impact_analysis` · `get_risk_analysis` · `get_project_context` · `get_cognition_pack` · `refresh_scan`

### Phase 2 — Memory + Human Approval
`remember_business_context` · `approve_memory` · `recall_context` · `remember_team_decision` · `list_memory` · `forget_memory`

### Phase 3 — Workspace + Graph + Approval Queue
`get_workspace_context` · `get_cross_repo_impact` · `export_graph` · `request_approval` · `check_approval` · `approve_request` · `reject_request` · `list_approvals`
