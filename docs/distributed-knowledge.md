# 15 — Distributed Knowledge (Phase 4.A — ✅ implemented)

> Reality: dev ไม่ได้ clone ทุก repo มาทำงานพร้อมกัน
> เขา clone ที่ละ repo — แต่ยังต้องการ memory + decisions + topology ของทีม

## Layout

```text
~/.knowai/                              ← user-level central store
  workspaces/
    my-product/
      workspace.toml                     ← topology (รู้ว่ามี repo อะไรบ้าง)
      memory.json                        ← shared decisions
      approvals.json                     ← shared approval queue
      scans/                             ← per-repo scan cache (Phase 4.B)
      packs/                             ← team-custom cognition packs

<any-project-repo>/
  .knowai/
    config.toml                          ← pointer to workspace (commit เข้า git)
```

Override default `~/.knowai` ด้วย env var: `KNOWLYX_HOME=/custom/path`

## Workflow

```bash
# 1. Tech lead สร้าง workspace ครั้งเดียว
knowai workspace create my-product
# → ~/.knowai/workspaces/my-product/

# 2. แก้ workspace.toml ใน ~/.knowai/workspaces/my-product/
#    ระบุ [[repos]] ทั้งหมด + [[dependencies]]

# 3. แต่ละ dev clone repo มาทำงาน → link
git clone git@github.com:company/api.git
cd api
knowai link my-product --role backend --domains billing,auth --critical
# → สร้าง .knowai/config.toml (commit เข้า git)

# 4. ใช้งานปกติ — Knowai resolve workspace อัตโนมัติ
knowai analyze "rename users.email"
# → อ่าน memory จาก ~/.knowai/workspaces/my-product/memory.json
# → รู้ topology ของ web/mobile/worker แม้ไม่ได้ clone
```

## Concurrency safety (v0.5+)

All writes ไปยัง `memory.json` / `approvals.json` ป้องกันด้วย:

1. **File lock** cross-platform — `fcntl` POSIX / `msvcrt` Windows
2. **Atomic write** — write temp ก่อน `os.replace()` → readers เห็น old หรือ new เท่านั้น, ไม่มี half-written
3. **Read-modify-write under lock** — ทุก save re-read disk → mutate → atomic write → **ไม่มี lost update** แม้ 2 sessions save พร้อมกัน

**Approve/reject fail-safe:** once REJECTED → stays rejected

- `approve(id)` หลัง reject เป็น no-op (return entry เดิมที่ rejected)
- `auto_merge_json` ใน git sync ก็เคารพกฎเดียวกัน (reject ชนะเสมอ, ไม่สน timestamp)

→ กันเคส: Dev A approve → Dev B reject เพราะเหตุผลที่ถูกต้อง → คนอื่น re-approve โดยไม่ตั้งใจ → bad change ออก production

## Memory schema v2 (auto-migrated จาก v1)

```json
{
  "version": 2,
  "entries": {
    "abc123": { "kind": "team_decision", "domain": "billing", "title": "...", ... }
  },
  "syntheses": {
    "billing": {
      "summary": "Team uses Stripe Billing for B2C, Stripe Connect for marketplaces. Refunds over $1000 need finance approval. All payment calls require idempotency keys.",
      "key_themes": ["stripe", "idempotency", "finance-approval"],
      "open_questions": ["Subscription proration policy?"],
      "synthesized_at": "2026-05-22T...",
      "synthesized_by": "ai",
      "entry_count_at_synthesis": 12,
      "stale": false
    }
  }
}
```

### Synthesis populate ยังไง? — Delegate-to-Claude pattern

**Knowai ไม่มี LLM ใน core** — AI agent ของคุณ (Claude/Cursor/etc.) เป็นคน synthesize:

1. AI call `get_domain_knowledge("billing")`
2. Knowai ส่ง raw entries + synthesis status (stale หรือ fresh)
3. ถ้า stale หรือไม่มี → tool result บอก AI ให้ distill themes/conflicts/open-questions
4. AI call `save_synthesis(domain, summary, themes, questions)` → cache
5. ทุก session ถัดไปได้ cached synthesis (จน entry ใหม่มาถึง → mark stale → re-synthesize)

→ ได้คุณภาพ LLM โดยที่ Knowai ไม่มี dependency LLM (ไม่ต้อง API key, ไม่มีค่าใช้จ่าย, ไม่ vendor lock-in)

### Risk upgrade-only rule

`analyze_intent` return `risk_policy` field — AI ต้องเคารพ:

```text
proceed → warn → ask → reject  (severity order)
```

AI ทำให้ strict ขึ้นได้ (เลื่อนขวา) ตาม historical context AI **ห้าม** ทำให้หลวมลง (เลื่อนซ้าย) Knowai decision คือ floor

## Backward compatibility

ของเดิมยังใช้ได้หมด:

- ถ้า repo ไม่มี `.knowai/config.toml` → fallback ใช้ `<repo>/.knowai/memory.json` แบบเดิม
- ถ้า `knowai.toml` อยู่ root folder ที่ครอบ repo → ใช้ pattern เดิม (siblings layout)
- ทุก MCP tool + CLI command ยัง accept `repo_path` argument เหมือนเดิม

## CLI commands ใหม่

| Command | หน้าที่ |
| --- | --- |
| `knowai workspace create <name>` | สร้าง central workspace ที่ `~/.knowai/workspaces/<name>/` |
| `knowai workspace list` | list central workspaces ทั้งหมด |
| `knowai link <workspace>` | link repo ปัจจุบันไปยัง central workspace |
| `knowai unlink` | ลบ `.knowai/config.toml` |
| `knowai migrate` | ย้าย legacy `<repo>/.knowai/memory.json` → central |

## Files ที่สร้างใน Phase 4.A

| File | หน้าที่ |
| --- | --- |
| [src/knowai/paths.py](../src/knowai/paths.py) | central path resolver (cross-platform, KNOWLYX_HOME env) |
| [src/knowai/link/config.py](../src/knowai/link/config.py) | LinkConfig + read/write `.knowai/config.toml` |
| [src/knowai/link/resolver.py](../src/knowai/link/resolver.py) | walk up from cwd → resolve workspace (or fall back to legacy) |
| [tests/test_paths.py](../tests/test_paths.py) | path resolution tests |
| [tests/test_link.py](../tests/test_link.py) | link config + integration tests |

## Files ที่แก้ใน Phase 4.A

| File | Change |
| --- | --- |
| [src/knowai/memory/store.py](../src/knowai/memory/store.py) | `create_store()` resolves workspace automatically |
| [src/knowai/approval/queue.py](../src/knowai/approval/queue.py) | `get_queue()` resolves workspace automatically |
| [src/knowai/workspace/config_loader.py](../src/knowai/workspace/config_loader.py) | `load()` falls back to central; new `load_central()` |
| [src/knowai/cli/main.py](../src/knowai/cli/main.py) | new commands: `workspace create/list`, `link`, `unlink`, `migrate` |

## Trade-offs

| Approach | ข้อดี | ข้อเสีย |
| --- | --- | --- |
| Central local (Phase 4.A) | Zero infra, work offline | Knowledge ไม่ sync ข้ามเครื่อง |
| + Git sync (Phase 4.C) | Version control, easy sync | ต้อง pull/push manual |
| + Cloud (Phase 5) | Real-time sync, web UI | ต้อง host server + auth |

## Phase 4.B — Cached scans (planned)

ปัจจุบัน `WorkspaceScanner` skip repo ที่ไม่มีใน disk — แต่ AI ยังตอบ "ใน web repo มี component อะไร" ไม่ได้ถ้า web ไม่ได้ clone

แก้ด้วย: persistent scan cache ที่ `~/.knowai/workspaces/<name>/scans/<repo>.json` — รัน scan บน CI หรือเครื่อง tech lead 1 ครั้ง, push เข้า central → dev คนอื่นใช้ cache นั้นได้แม้ไม่ clone repo นั้นๆ

## Phase 4.C — Git sync (planned)

```bash
# ผูก ~/.knowai/workspaces/my-product/ กับ git remote
knowai sync init --remote git@github.com:company/knowai-shared.git

# Sync (pull → merge → push)
knowai sync pull
knowai sync push
knowai sync status
```

Conflict resolution: timestamp-based merge สำหรับ memory entries (newer wins, log conflicts)

## Real-world usage

**Scenario:** Junior dev เริ่มทำ feature ใหม่

```bash
# Onboarding
git clone git@github.com:company/api.git
cd api
cat .knowai/config.toml
# workspace = "my-product"
# (committed by tech lead เดือนที่แล้ว)

# AI session ใน Claude Code
# Junior: "add password reset endpoint"
# → analyze_intent resolved workspace 'my-product' from .knowai/config.toml
# → injects memory: "team uses SendGrid, fallback SES" (approved 2 weeks ago)
# → injects topology: web + mobile consume /auth/* endpoints
# → suggests: backward-compat strategy because mobile users may be on old version
# → AI gen ถูก first try
```

Junior ไม่ต้องรู้เลยว่า memory/topology อยู่ที่ไหน — Knowai resolve อัตโนมัติ
