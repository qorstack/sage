# 14 — Real-world Usage Examples

7 scenarios ที่ dev ทั่วโลกเจอทุกวัน — ไม่ว่าทำ startup หรือ enterprise, ใช้ stack ไหนก็ตาม

## Scenario 1: "We already have a helper for that"

**Pain ที่เจอทุกทีม:** PR review comment ที่เจอบ่อยที่สุดในโลก

**Situation:** AI gen `formatCurrency()` ใหม่ — ทั้งที่ team มี `utils/money.ts` อยู่แล้ว 2 ปี

**ปกติ:**

- AI grep "currency" ไม่เจอเพราะไฟล์ชื่อ `money.ts`
- Gen utility ซ้ำ
- PR review: "we have utils/money.ts, please use that"
- AI revert, rewrite
- เสีย review cycle 1 รอบ

**With Knowai:**

```text
analyze_intent("display product price formatted")
  → reusable_assets[display]:
    • utils/money.ts (formatCurrency, parseAmount) — used in 47 files
    • hooks/useCurrency.ts (locale-aware)
  → AI imports existing utility → first-try PR approved
```

---

## Scenario 2: AI ignores project conventions

**Pain:** ทุก codebase มี convention ของตัวเอง — `CLAUDE.md` / `.cursorrules` / `AGENTS.md` ก็เขียน แต่ AI ลืม

**Situation:** Codebase ใช้ TanStack Query สำหรับทุก data fetching แต่ AI gen code ใช้ `useState + useEffect + fetch`

**ปกติ:**

- AI อ่าน CLAUDE.md แค่บางครั้ง
- Gen `useEffect(() => { fetch(...) })` pattern เก่า
- Reviewer: "use useQuery please"
- AI rewrite

**With Knowai:**

```text
get_conventions(repo_path)
  → Detected (from package.json + grep):
    • @tanstack/react-query installed + used in 89 files
    • forbidden: raw fetch in components
    • pattern: useQuery for GET, useMutation for POST/PUT/DELETE
  → MCP returns tool result (not markdown) — AI trusts it
  → Generated code uses useQuery first-try
```

→ ใช้ได้กับทุก convention: ESLint rules, import order, naming, testing library choice

---

## Scenario 3: Database migration breaks downstream

**Pain:** Universal across any team with microservices or shared DB

**Situation:** Backend dev rename column `users.email` → `users.email_address`

**ปกติ:**

- Dev ทำ Alembic/Prisma migration
- Deploy backend ✅
- 5 นาทีต่อมา: analytics service crash (ETL อ่าน `email`)
- 10 นาทีต่อมา: notification worker crash
- 15 นาทีต่อมา: admin dashboard 500
- Slack ระเบิด → rollback migration → painful

**With Knowai:**

```bash
$ knowai workspace impact api --change "rename users.email to email_address"

Cascade affected:
  ⚠️ analytics-service (queries users.email in 6 places)
  ⚠️ notification-worker (templates reference {{email}})
  ⚠️ admin-dashboard (CSV export column)
  ⚠️ marketing-service (Segment integration)

Risk: HIGH → submit approval
Suggested workflow:
  1. Add new column, keep old (dual-write)
  2. Migrate consumers one by one
  3. Drop old column after all migrated
```

→ Zero downtime migration, no firefight

---

## Scenario 4: AI hallucinates imports/functions

**Pain:** อันนี้ดังที่สุดในชุมชน AI coding — "AI made up a function that doesn't exist"

**Situation:** AI ขึ้นบรรทัด `import { validateEmail } from '@/utils/validators'` ทั้งที่ไม่มีไฟล์นี้

**ปกติ:**

- Type error / import error ตอน run
- Dev เสียเวลา debug → realize AI hallucinate
- บอก AI fix → AI gen function ใหม่
- บางครั้ง gen ซ้ำของที่มีอยู่อีก (กลับไป Scenario 1)

**With Knowai:**

```text
Before write → validate_generated_code(code, repo_path)
  → Violations:
    ❌ Import '@/utils/validators' does not exist
    💡 Suggestion: '@/lib/validation' has validateEmail (used in 12 places)
    💡 Or: 'zod' is installed — prefer z.string().email() for new code

  → AI fixes before write → no hallucinated import ever committed
```

---

## Scenario 5: Refactor touches more than expected

**Pain:** "I'll just rename this function" → 2 hours later, found 47 callers

**Situation:** Junior dev ขอ AI "rename `processOrder()` to `submitOrder()`"

**ปกติ:**

- AI rename ในไฟล์ที่ user เปิดอยู่
- Push, CI fail (12 ที่เรียกชื่อเก่า)
- AI ค่อยๆไล่แก้
- ลืม mock ใน test files
- Rerun, fail again

**With Knowai:**

```text
analyze_intent("rename processOrder to submitOrder")
  → impact:
    • 12 production files import processOrder
    • 8 test files reference it
    • 3 mock fixtures
    • 1 OpenAPI spec mentions it
  → workflow:
    1. Update implementation
    2. Update all 12 imports (list provided)
    3. Update tests (list provided)
    4. Update mocks
    5. Regenerate OpenAPI types
  → AI does all in one pass, single PR
```

---

## Scenario 6: New dev onboarding

**Pain:** Every team has this — "where do I even start?"

**Situation:** Junior joins, given Slack + Notion + 80k LOC repo

**ปกติ:**

- อ่าน README → ไม่ update แล้ว
- ถาม senior 30 ครั้งวันแรก
- 1-2 สัปดาห์กว่าจะกล้าเปิด PR
- PR แรก review 3 รอบ

**With Knowai:**

```bash
$ knowai scan .
Languages: TypeScript, Python
Frameworks: Next.js 15 (app router), FastAPI, Prisma
Architecture: modular_monolith
Domains: user, billing, content, analytics, admin
Conventions: 23 detected
  • App Router only (no pages/)
  • Server Components default, "use client" explicit
  • Forms: react-hook-form + zod
  • Data fetching: TanStack Query (client) / direct Prisma (server)
  • State: Zustand (no Redux)
  • Styling: Tailwind only (no CSS modules, no styled-components)
Reusable assets: 124
  • UI: 47 (shadcn-based)
  • Hooks: 31
  • Utils: 28
  • Server actions: 18
Forbidden patterns:
  • console.log (use logger)
  • any type (use unknown + zod parse)
  • direct DB in components (server actions only)

$ knowai graph mermaid > docs/architecture.md
```

→ Day 1 = senior-level mental model. PR แรกผ่าน first review

---

## Scenario 7: Breaking API contract silently

**Pain:** Universal สำหรับ team ที่มี frontend/backend แยก

**Situation:** Backend เปลี่ยน response shape — `{ data: [...] }` → `[...]`

**ปกติ:**

- Backend dev คิดว่า "minor improvement"
- Deploy backend
- Frontend ทั้งหมดพัง production
- ไม่มี TypeScript error เพราะ types เป็น `any` หลัง JSON parse

**With Knowai:**

```text
analyze_intent("flatten API response remove data wrapper")
  → impact:
    • frontend consumers: 23 components use response.data
    • generated TypeScript client needs regen
    • mobile app (React Native) consumes same endpoint
    • Postman collection used by QA
  → memory recall: "API contract changes require 2-week deprecation"
  → risk: HIGH → ASK
  → suggested:
    1. Add new endpoint /v2/...
    2. Keep /v1 with deprecation header
    3. Migrate consumers
    4. Remove /v1 after 2 weeks
```

→ ไม่มี surprise breakage, frontend team รู้ตั้งแต่ก่อน backend แตะ code

---

## Summary: Universal pain → Knowai gain

| Pain ที่เจอทุกที่ | Knowai solution |
| --- | --- |
| "We have a helper for that" | `get_reusable_assets` injects existing utilities |
| AI ignores CLAUDE.md / cursorrules | MCP tool result (AI trusts > markdown) |
| Migration breaks downstream | `get_cross_repo_impact` shows blast radius |
| AI hallucinates imports | `validate_generated_code` blocks before write |
| Refactor missing call sites | `get_impact_analysis` lists all callers |
| Onboarding 2 weeks | `scan` + `graph` = 5 min mental model |
| API contract silent break | Risk gate + deprecation workflow |

**The common thread:** AI ปัจจุบันมี "code knowledge" แต่ไม่มี "system cognition"
Knowai เติม cognition layer — ใช้ได้กับทุก stack, ทุก team size, ทุกอุตสาหกรรม
