# 04 — Scanner Layer

📂 [src/knowlyx/scanner/](../src/knowlyx/scanner/)

อ่าน repo → infer ทุกอย่างที่ static analysis ตอบได้ โดยไม่ต้องถามคน

## Files

| File | หน้าที่ |
| --- | --- |
| `repo_scanner.py` | ตรวจ language, framework, architecture pattern, domains, API clients, forbidden patterns |
| `convention_detector.py` | ตรวจ naming, imports, architecture, lint, test patterns |
| `asset_detector.py` | ตรวจ reusable components/hooks/utils/services + tag ตาม domain |

## ตรวจอะไรได้

### Languages & Frameworks

- **Python:** FastAPI, Django, Flask
- **TypeScript/JS:** Next.js, React, NestJS, Express
- **Go, Rust, Java** — basic detection

### Architecture Patterns

- `clean_architecture` — มี `domain/`, `application/`, `infrastructure/`
- `ddd` — มี `aggregate`, `value_object`, `bounded_context`
- `modular_monolith` — top-level modules แยกกัน
- `layered` — controller/service/repository
- `microservices` — multi-repo + service boundary clear

### Domains (จาก folder names + keywords)

`auth`, `billing`, `user`, `notification`, `webhook`, `worker`, `audit`, `search`, `analytics`, `admin` ฯลฯ

### Reusable Assets

- React components, hooks, utils, services
- Tag ตาม domain ที่อยู่ใกล้ที่สุด
- Track usage count (กี่ที่ import)

### Conventions

- Naming (camelCase vs snake_case vs kebab-case)
- Import rules (absolute vs relative, allowed paths)
- Lint rules (จาก `.eslintrc`, `pyproject.toml`, `ruff.toml`)
- Test patterns (vitest/jest/pytest, location, naming)

### Forbidden Patterns

- `console.log` ใน production code
- Direct `fetch`/`axios` เมื่อมี TanStack Query / generated client
- Hardcoded secrets
- `any` type ใน TypeScript

## Implementation tech

- **Tree-sitter** — สำหรับ accurate parsing (planned upgrade, ตอนนี้ใช้ regex + ast)
- **ripgrep** — fast text scan
- **Python ast module** — parse Python ตรงๆ

## Output structure

```python
ScanResult(
    repo_path="/path/to/repo",
    languages=["python", "typescript"],
    frameworks=["fastapi", "nextjs"],
    architecture="modular_monolith",
    domains=["billing", "auth", "notification"],
    api_clients=["openapi-generated"],
    conventions=[Convention(...), ...],
    assets=[Asset(...), ...],
    forbidden_patterns=[...],
)
```

## Cache

- `_state` dict ใน `mcp/server.py` และ `api/main.py`
- Key = `repo_path`
- Invalidate via `refresh_scan(repo_path)` MCP tool หรือ `knowlyx scan` CLI

## Real-world usage

```bash
# CLI
uv run knowlyx scan /path/to/repo

# Output:
# Languages: python, typescript
# Frameworks: fastapi, nextjs
# Architecture: modular_monolith
# Domains: billing, auth, notification, user (4)
# Conventions: 12 detected
# Reusable assets: 47 (components: 23, hooks: 8, utils: 16)
# Forbidden patterns: 3 violations
```

```python
# Python
from knowlyx.scanner import RepoScanner

scanner = RepoScanner()
result = scanner.scan("/path/to/repo")
print(result.architecture)  # "modular_monolith"
print([a.name for a in result.assets if a.domain == "billing"])
# ['InvoiceCard', 'usePricing', 'formatCurrency']
```

**Scenario จริง:** Onboard repo ใหม่

1. Dev clone repo เข้ามา
2. `uv run knowlyx scan .` → เห็นภาพรวมใน 3 วินาที (architecture, domains, conventions)
3. ไม่ต้องอ่าน README 30 หน้า
