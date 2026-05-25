# 09 — Multi-Repo Workspace

📂 [src/knowai/workspace/](../src/knowai/workspace/)

โปรเจกต์จริงไม่ใช่ repo เดียว — มี api + web + mobile + worker + admin
Knowai ต้องเห็นทั้งหมดและรู้ว่าใครคุยกับใคร

## knowai.toml

วางที่ root ของ workspace (โฟลเดอร์ที่ครอบทุก repo):

```toml
name = "my-product"

[[repos]]
name = "api"
path = "./api"
role = "backend"
domains = ["billing", "auth", "user"]
critical = true

[[repos]]
name = "web"
path = "./web"
role = "frontend"

[[repos]]
name = "mobile"
path = "./mobile"
role = "frontend"

[[repos]]
name = "worker"
path = "./worker"
role = "worker"
domains = ["billing", "notification"]

[[repos]]
name = "admin"
path = "./admin"
role = "frontend"

[[dependencies]]
from = "web"
to = "api"
type = "api"

[[dependencies]]
from = "mobile"
to = "api"
type = "api"

[[dependencies]]
from = "worker"
to = "api"
type = "event"

[[dependencies]]
from = "admin"
to = "api"
type = "api"
```

## WorkspaceScanner

Scan ทุก repo **parallel** → build cross-repo NetworkX graph

**Inferred edges อัตโนมัติ:**

- Frontend ที่มี generated API client (เจอ `src/api/generated/`) → backend
- Worker ที่ share domain กับ source repo → source repo
- Declared dependencies จาก `knowai.toml`

## CrossRepoImpactAnalyzer

Input: `changed_repo + change description`
Output: รายการ repo ที่กระทบ + criticality

```python
analyzer.analyze(
    changed_repo="api",
    change="rename users.email to email_address"
)
# →
# {
#   "directly_affected": ["api"],
#   "cascade_affected": ["web", "mobile", "worker", "admin"],
#   "critical_repos_affected": ["api"],
#   "actions_required": [
#     "regenerate OpenAPI client in web/mobile",
#     "update worker email template references",
#     "update admin CSV export schema"
#   ]
# }
```

## CLI

```bash
# Init knowai.toml อัตโนมัติ (Phase 4 — ยังไม่มี)
knowai workspace init

# Scan ทุก repo
knowai workspace scan

# Cross-repo impact
knowai workspace impact api --change "rename users.email column"

# Graph
knowai workspace graph
knowai workspace graph react_flow --json
knowai workspace graph mermaid
```

## MCP tools

| Tool | use |
| --- | --- |
| `get_workspace_context(workspace_path)` | overview ทุก repo |
| `get_cross_repo_impact(changed_repo, change, workspace_path)` | blast radius |
| `export_graph("react_flow", workspace_path=...)` | visualize |

## Real-world usage

**Scenario:** Backend dev จะ rename DB column

```bash
$ knowai workspace impact api --change "rename users.email → email_address"

Workspace: my-product
Changed repo: api (CRITICAL)

Directly affected:
  - api/src/auth/repository.py
  - api/src/user/repository.py
  - api/migrations/

Cascade affected:
  ⚠️ web (OpenAPI consumer)
    → must regenerate: npm run gen:api
    → must test: src/profile/, src/settings/

  ⚠️ mobile (React Native, OpenAPI consumer)
    → must regenerate + ship new app version
    → backward compat needed (old app still in production)

  ⚠️ worker (email templates)
    → templates reference {{user.email}}
    → must update: templates/welcome.html, templates/password_reset.html

  ℹ️ admin (CSV export)
    → column header "email" → "email_address"
    → may break customer integrations using exports

Actions required:
  1. Add new column, dual-write period
  2. Migrate consumers (mobile last — old app compat)
  3. Drop old column after 30 days
  4. Document column rename in CHANGELOG

Risk: HIGH → recommend approval queue
```

→ ก่อน Knowai: dev ลืม update mobile → users on old app version พัง production
→ หลัง Knowai: เห็นชัดก่อนเริ่ม + plan rollout safe
