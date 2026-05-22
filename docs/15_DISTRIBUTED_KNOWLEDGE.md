# 15 — Distributed Knowledge (Phase 4.A — ✅ implemented)

> Reality: dev ไม่ได้ clone ทุก repo มาทำงานพร้อมกัน
> เขา clone ที่ละ repo — แต่ยังต้องการ memory + decisions + topology ของทีม

## Layout

```text
~/.knowlyx/                              ← user-level central store
  workspaces/
    my-product/
      workspace.toml                     ← topology (รู้ว่ามี repo อะไรบ้าง)
      memory.json                        ← shared decisions
      approvals.json                     ← shared approval queue
      scans/                             ← per-repo scan cache (Phase 4.B)
      packs/                             ← team-custom cognition packs

<any-project-repo>/
  .knowlyx/
    config.toml                          ← pointer to workspace (commit เข้า git)
```

Override default `~/.knowlyx` ด้วย env var: `KNOWLYX_HOME=/custom/path`

## Workflow

```bash
# 1. Tech lead สร้าง workspace ครั้งเดียว
knowlyx workspace create my-product
# → ~/.knowlyx/workspaces/my-product/

# 2. แก้ workspace.toml ใน ~/.knowlyx/workspaces/my-product/
#    ระบุ [[repos]] ทั้งหมด + [[dependencies]]

# 3. แต่ละ dev clone repo มาทำงาน → link
git clone git@github.com:company/api.git
cd api
knowlyx link my-product --role backend --domains billing,auth --critical
# → สร้าง .knowlyx/config.toml (commit เข้า git)

# 4. ใช้งานปกติ — Knowlyx resolve workspace อัตโนมัติ
knowlyx analyze "rename users.email"
# → อ่าน memory จาก ~/.knowlyx/workspaces/my-product/memory.json
# → รู้ topology ของ web/mobile/worker แม้ไม่ได้ clone
```

## Backward compatibility

ของเดิมยังใช้ได้หมด:

- ถ้า repo ไม่มี `.knowlyx/config.toml` → fallback ใช้ `<repo>/.knowlyx/memory.json` แบบเดิม
- ถ้า `knowlyx.toml` อยู่ root folder ที่ครอบ repo → ใช้ pattern เดิม (siblings layout)
- ทุก MCP tool + CLI command ยัง accept `repo_path` argument เหมือนเดิม

## CLI commands ใหม่

| Command | หน้าที่ |
| --- | --- |
| `knowlyx workspace create <name>` | สร้าง central workspace ที่ `~/.knowlyx/workspaces/<name>/` |
| `knowlyx workspace list` | list central workspaces ทั้งหมด |
| `knowlyx link <workspace>` | link repo ปัจจุบันไปยัง central workspace |
| `knowlyx unlink` | ลบ `.knowlyx/config.toml` |
| `knowlyx migrate` | ย้าย legacy `<repo>/.knowlyx/memory.json` → central |

## Files ที่สร้างใน Phase 4.A

| File | หน้าที่ |
| --- | --- |
| [src/knowlyx/paths.py](../src/knowlyx/paths.py) | central path resolver (cross-platform, KNOWLYX_HOME env) |
| [src/knowlyx/link/config.py](../src/knowlyx/link/config.py) | LinkConfig + read/write `.knowlyx/config.toml` |
| [src/knowlyx/link/resolver.py](../src/knowlyx/link/resolver.py) | walk up from cwd → resolve workspace (or fall back to legacy) |
| [tests/test_paths.py](../tests/test_paths.py) | path resolution tests |
| [tests/test_link.py](../tests/test_link.py) | link config + integration tests |

## Files ที่แก้ใน Phase 4.A

| File | Change |
| --- | --- |
| [src/knowlyx/memory/store.py](../src/knowlyx/memory/store.py) | `create_store()` resolves workspace automatically |
| [src/knowlyx/approval/queue.py](../src/knowlyx/approval/queue.py) | `get_queue()` resolves workspace automatically |
| [src/knowlyx/workspace/config_loader.py](../src/knowlyx/workspace/config_loader.py) | `load()` falls back to central; new `load_central()` |
| [src/knowlyx/cli/main.py](../src/knowlyx/cli/main.py) | new commands: `workspace create/list`, `link`, `unlink`, `migrate` |

## Trade-offs

| Approach | ข้อดี | ข้อเสีย |
| --- | --- | --- |
| Central local (Phase 4.A) | Zero infra, work offline | Knowledge ไม่ sync ข้ามเครื่อง |
| + Git sync (Phase 4.C) | Version control, easy sync | ต้อง pull/push manual |
| + Cloud (Phase 5) | Real-time sync, web UI | ต้อง host server + auth |

## Phase 4.B — Cached scans (planned)

ปัจจุบัน `WorkspaceScanner` skip repo ที่ไม่มีใน disk — แต่ AI ยังตอบ "ใน web repo มี component อะไร" ไม่ได้ถ้า web ไม่ได้ clone

แก้ด้วย: persistent scan cache ที่ `~/.knowlyx/workspaces/<name>/scans/<repo>.json` — รัน scan บน CI หรือเครื่อง tech lead 1 ครั้ง, push เข้า central → dev คนอื่นใช้ cache นั้นได้แม้ไม่ clone repo นั้นๆ

## Phase 4.C — Git sync (planned)

```bash
# ผูก ~/.knowlyx/workspaces/my-product/ กับ git remote
knowlyx sync init --remote git@github.com:company/knowlyx-shared.git

# Sync (pull → merge → push)
knowlyx sync pull
knowlyx sync push
knowlyx sync status
```

Conflict resolution: timestamp-based merge สำหรับ memory entries (newer wins, log conflicts)

## Real-world usage

**Scenario:** Junior dev เริ่มทำ feature ใหม่

```bash
# Onboarding
git clone git@github.com:company/api.git
cd api
cat .knowlyx/config.toml
# workspace = "my-product"
# (committed by tech lead เดือนที่แล้ว)

# AI session ใน Claude Code
# Junior: "add password reset endpoint"
# → analyze_intent resolved workspace 'my-product' from .knowlyx/config.toml
# → injects memory: "team uses SendGrid, fallback SES" (approved 2 weeks ago)
# → injects topology: web + mobile consume /auth/* endpoints
# → suggests: backward-compat strategy because mobile users may be on old version
# → AI gen ถูก first try
```

Junior ไม่ต้องรู้เลยว่า memory/topology อยู่ที่ไหน — Knowlyx resolve อัตโนมัติ
