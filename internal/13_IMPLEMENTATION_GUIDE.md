# 13 — Implementation Guide

Step-by-step ต่อจากนี้ — ทำตามลำดับ

## Sprint 0 — Verify ของที่มีอยู่ (1-2 วัน)

ของ Phase 1-3 ทั้งหมด เขียนแล้วแต่ยังไม่ run

### Step 1: Sync deps

```bash
cd /path/to/knowai
uv sync
uv sync --extra vector   # ทดสอบ optional ด้วย
```

**ถ้า fail:** อ่าน error → fix `pyproject.toml` (น่าจะเป็น version conflict)

### Step 2: Run tests

```bash
uv run pytest -v
```

**Expected:** 7 test files, ~50 tests
**ถ้า fail:** จัดลำดับ priority — test_scanner → test_reasoning → test_memory → test_packs → test_workspace → test_approval → test_graph_exporter

### Step 3: Lint

```bash
uv run ruff check src/
uv run ruff format src/
```

### Step 4: Smoke test CLI

```bash
uv run knowai scan .                              # scan self
uv run knowai analyze "add OTP" --repo .
uv run knowai impact "fix payment 501" --repo .
uv run knowai pack payment
uv run knowai memory list --repo .
```

### Step 5: Smoke test MCP

```bash
# Terminal 1
uv run knowai mcp --repo .

# Terminal 2 (mock client)
# ใช้ fastmcp tester หรือ Claude Code จริง
```

### Step 6: Integration test กับ Claude Code

1. เพิ่ม MCP config ใน Claude Code project test
2. เปิด session → ลองถาม "เพิ่ม OTP login"
3. ดูว่า Claude call `analyze_intent` จริงไหม
4. ดู cognition report ที่ return กลับ

**Definition of done:** Claude Code call tools ครบ flow, ไม่มี exception

---

## Sprint 1 — Complete REST API + Init Command (3-5 วัน)

### Step 7: เพิ่ม REST routes Phase 2-3

ไฟล์: [src/knowai/api/main.py](../src/knowai/api/main.py)

ปัจจุบันมีแค่ Phase 1 routes — เพิ่ม:

```python
# Phase 2
POST /memory/save
POST /memory/approve
POST /memory/recall
POST /memory/decide
GET  /memory/list
DELETE /memory/{entry_id}
GET  /packs/{domain}

# Phase 3
POST /workspace/scan
POST /workspace/impact
POST /graph/export
POST /approval/request
GET  /approval/{request_id}
POST /approval/{request_id}/approve
POST /approval/{request_id}/reject
GET  /approval/list
```

Mirror โครงสร้างจาก MCP tools — ใช้ Pydantic models เดียวกัน

### Step 8: `knowai init` command

```bash
knowai init                    # ใน single repo → สร้าง .knowai/ + auto-detect
knowai init --workspace        # ใน workspace root → สร้าง knowai.toml + auto-discover repos
```

ไฟล์: [src/knowai/cli/](../src/knowai/cli/) — เพิ่ม `init_cmd.py`

Auto-discovery logic สำหรับ workspace:
- scan subdirectories ที่มี `.git/`
- detect role จาก `package.json` (next → frontend), `pyproject.toml` (fastapi → backend), worker keyword
- ถาม user confirm ก่อน write

### Step 9: GitHub Actions CI

ไฟล์: `.github/workflows/test.yml`

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --extra vector
      - run: uv run pytest -v
      - run: uv run ruff check src/
```

ไฟล์: `.github/workflows/publish.yml` (trigger ตอน tag)

### Step 10: PyPI publish dry run

```bash
uv build
uv publish --dry-run   # ตรวจ metadata
```

---

## Sprint 2 — Phase 4.1: AI Self-Review (1-2 สัปดาห์)

### Step 11: `validate_generated_code` MCP tool

ไฟล์ใหม่: `src/knowai/validation/code_validator.py`

```python
class CodeValidator:
    def validate(self, code: str, repo_path: str, language: str) -> ValidationReport:
        violations = []
        violations += self._check_conventions(code, repo_path)
        violations += self._check_forbidden_patterns(code, repo_path)
        violations += self._check_reuse(code, repo_path)  # ใช้ asset ที่มีอยู่หรือเปล่า
        violations += self._check_imports(code, repo_path)
        return ValidationReport(passed=len(violations)==0, violations=violations)
```

MCP tool:
```python
@mcp.tool()
def validate_generated_code(code: str, repo_path: str, language: str = "python"):
    """Call BEFORE writing files. Returns violations + fix suggestions."""
```

### Step 12: Encourage AI to call before write

เพิ่มใน MCP server intro / tool descriptions:
> "ALWAYS call `validate_generated_code` before writing any code file"

---

## Sprint 3 — Phase 4.3: Architectural Enforcement Hooks (1 สัปดาห์)

### Step 13: `knowai commit-check` command

```bash
knowai commit-check    # อ่าน staged files + check ว่า AI ได้ผ่าน cognition pipeline
```

Logic:
- อ่าน `.knowai/last_cognition.json` (engine บันทึกทุกครั้งที่ call analyze_intent)
- เทียบ timestamp กับ staged files mtime
- ถ้า staged files แก้หลัง cognition report → require new analyze_intent
- ถ้า decision == "reject" หรือ "ask" และไม่มี approval → block commit

### Step 14: pre-commit hook integration

```yaml
# .pre-commit-hooks.yaml
- id: knowai-cognition-check
  name: Knowai Cognition Check
  entry: knowai commit-check
  language: system
  stages: [commit]
```

### Step 15: GitHub Action enforcement

```yaml
- name: Knowai Cognition Gate
  run: knowai commit-check --strict
```

---

## Sprint 4+ — Frontend UI (3-4 สัปดาห์)

### Step 16: Bootstrap Next.js app

```bash
cd packages/
npx create-next-app@latest knowai-ui --typescript --tailwind --app
cd knowai-ui
npx shadcn@latest init
npm install reactflow zustand recharts
```

### Step 17: Pages

| Route | Purpose |
|---|---|
| `/` | Workspace overview (repo cards) |
| `/repo/[name]` | Single repo cognition |
| `/graph` | React Flow visualization |
| `/memory` | Memory browser + approve queue |
| `/approvals` | Approval inbox |

### Step 18: Connect to REST API

ทุก page fetch จาก FastAPI ที่เราขยายใน Step 7

---

## Definition of done — ทั้ง roadmap

✅ `uv run pytest` ผ่านครบ
✅ Claude Code integration test ผ่าน (manual)
✅ Published to PyPI
✅ `uvx knowai mcp --repo .` ใช้ได้จากเครื่องไหนก็ได้
✅ AI self-review block bad code ก่อน write
✅ pre-commit hook enforce cognition
✅ UI visualize graph + manage approvals

→ Ship to public, write launch post, get first 100 users
