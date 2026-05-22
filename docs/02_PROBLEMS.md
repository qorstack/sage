# 02 — Problems Knowlyx Solves

7 ปัญหา core ที่ AI coding tools ปัจจุบันแก้ไม่ได้ — เจอกันทุกทีมทั่วโลก

## P1 — Business Understanding

**ปัญหา:** AI ไม่รู้ว่า "password reset" ในทีมนี้ต้องมีอะไรบ้าง — token expiry, rate limit, audit log, email provider

**Knowlyx แก้:** Cognition Packs (built-in 7 domains) + Memory (team-specific)

**ตัวอย่าง:**

```text
Request: "add password reset"
→ Pack `auth` inject: token expiry 15min, single-use, rate limit, audit log
→ Memory inject: "team uses SendGrid, fallback SES" (approved decision)
```

## P2 — Architecture Awareness

**ปัญหา:** AI เขียน `fetch('/api/...')` ทั้งที่ codebase ใช้ TanStack Query + generated TypeScript client

**Knowlyx แก้:** `ConventionDetector` ตรวจ stack + forbidden patterns

**ตัวอย่าง:**

```text
Detected (from package.json + usage):
- architecture: modular_monolith
- data layer: TanStack Query (used in 89 files)
- forbidden: raw fetch in components
- enforce: server actions for mutations
```

## P3 — UX/UI Pattern Cognition

**ปัญหา:** AI gen modal ที่ spacing, color, dark mode ไม่ตรงกับ design system ที่ใช้อยู่

**Knowlyx แก้:** Design cognition (Phase 4) — ตรวจ Tailwind config, shared/ui components, spacing scale

**ตัวอย่าง:**

```text
Detected:
- spacing scale: 4/8/16/24 (no arbitrary values)
- modal pattern: <Dialog> from @/components/ui (NOT raw HTML)
- dark mode: class-based via next-themes
- forms: react-hook-form + zod
```

## P4 — Reuse Awareness

**ปัญหา:** AI สร้าง `formatCurrency()` ใหม่ทั้งที่มี `utils/money.ts` อยู่แล้ว — comment ที่เจอบ่อยที่สุดใน PR review

**Knowlyx แก้:** `AssetDetector` + `get_reusable_assets(domain)`

**ตัวอย่าง:**

```text
Request: "display product price"
→ assets[billing]:
  - utils/money.ts (formatCurrency, parseAmount) — used in 47 files
  - hooks/useCurrency.ts (locale-aware)
  - components/PriceTag.tsx
→ AI: "reuse existing instead of creating new"
```

## P5 — Impact Awareness

**ปัญหา:** AI rename `users.email` → `users.email_address` โดยไม่รู้ว่า worker + analytics + admin dashboard อ่าน column เดิม

**Knowlyx แก้:** `ImpactAnalyzer` + cross-repo graph + cascade rules

**ตัวอย่าง:**

```text
Change: "rename users.email → email_address"
→ Impact:
  - api/src/auth/ ✓ (direct)
  - worker/email_templates ⚠️ (references {{email}})
  - analytics/etl ⚠️ (SELECT email FROM users)
  - admin/csv_export ⚠️ (column header)
→ Decision: ASK (cross-service breakage)
```

## P6 — AI Intent Safety

**ปัญหา:** AI run destructive migration หรือ rewrite auth middleware โดยไม่ pause ให้ human ดูก่อน

**Knowlyx แก้:** `RiskScorer` + `ApprovalQueue` — decision: `proceed/warn/ask/reject`

**ตัวอย่าง:**

```text
Request: "rewrite auth middleware to use JWT"
→ Risk: HIGH (touches auth + sessions + 12 dependent endpoints)
→ Decision: ASK
→ Knowlyx submit approval gate
→ AI poll until human approves
→ proceed only after approval
```

## P7 — Multi-Repo System Awareness

**ปัญหา:** Real product = api + web + mobile + worker + admin — AI เห็นแค่ repo เดียว

**Knowlyx แก้:** Workspace (`knowlyx.toml`) + cross-repo graph + inferred dependencies

**ตัวอย่าง:**

```text
Workspace: knowlyx.toml
→ scan: api, web, mobile, worker, admin (parallel)
→ inferred edges:
  - web → api (generated client detected)
  - mobile → api (OpenAPI consumer)
  - worker → api (shared schema)
  - admin → api (declared)
→ AI ถาม "change /users response shape" → ได้คำตอบครบทุก consumer
```

## ปัญหาที่ Knowlyx ยังไม่แก้ (Phase 4+)

| Problem | Status |
| --- | --- |
| Business conflict detection (feature ใหม่ขัด policy เก่า) | ❌ ยังไม่มีใครทำดี |
| Business evolution (track ว่า rule เปลี่ยนเมื่อไหร่/ทำไม) | ❌ |
| AI self-review ก่อน submit code | 🟡 บางตัวเริ่ม |
| Design system enforcement | ❌ |

→ นี่คือช่องว่างที่ Knowlyx ควรเป็น winner
