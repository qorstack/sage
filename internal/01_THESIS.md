# 01 — Product Thesis

## Two sentences ที่เป็นแกน

> **AI should not touch code before understanding the system.**
>
> **Knowledge is passive. Cognition must be enforced.**

ทุก feature ทุก decision ต้องสอบผ่าน 2 ประโยคนี้ — ถ้าไม่ผ่านคือไม่ใช่ Knowai

## What Knowai IS NOT

- ❌ AI coding assistant (Cursor/Copilot/Cline ทำดีกว่าแล้ว)
- ❌ Documentation generator
- ❌ Code search tool
- ❌ Linter
- ❌ Memory store เฉยๆ

## What Knowai IS

- ✅ **Enforcement layer** ที่ AI agents ต้องผ่านก่อนเขียน code
- ✅ **System cognition runtime** ที่ตอบคำถามแทน human ว่า "ระบบนี้ทำงานยังไง, ทำไม, ถ้าแก้แล้วกระทบไหน"
- ✅ **Decision gate** สำหรับ high-risk changes

## Why this matters

AI tools ปัจจุบันมี 3 อาการที่ทุกทีมเจอ:

1. **Generate ซ้ำของที่มีอยู่แล้ว** — AI gen `formatDate()` ใหม่ทั้งที่มี `utils/date.ts` อยู่แล้ว 2 ปี
2. **ละเมิด architecture conventions** — อ่าน CLAUDE.md / .cursorrules ไม่ครบ ก็เขียน `useEffect + fetch` แทนที่จะใช้ TanStack Query ที่ team ใช้อยู่
3. **Miss cross-service impact** — rename DB column โดยไม่รู้ว่า worker + analytics service อ่าน column เดิม

Knowai แก้ทั้ง 3 ด้วยการ **บังคับ AI ให้ call MCP tools ก่อน** ไม่ใช่หวังว่า AI จะอ่าน markdown (ซึ่งหลักฐานชี้ว่า AI ignore บ่อย)

## Core insight

AI ไม่ต้องการ **perfect memory** หรือ **full context**

AI ต้องการ **system intuition** แบบ senior engineer:

- "อันนี้น่าจะอยู่ใน billing domain"
- "billing เกี่ยวกับ webhook + audit + invoicing"
- "มี shared `MoneyInput` component อยู่แล้ว"
- "เปลี่ยน schema นี้อาจกระทบ background worker"

→ Knowai ให้ intuition นี้แบบ structured ผ่าน MCP tools

## Differentiator vs ตลาด

| Tool                          | Approach                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------- |
| AgentMemory / ctx0 / MemLayer | Persistent memory layer                                                         |
| Aictx                         | Repo context layer                                                              |
| **Knowai**                   | **Enforced cognition pipeline** (memory + reasoning + impact + risk + workflow) |

ตลาดส่วนใหญ่ solve "memory"
Knowai solve **"cognition + enforcement"** — ยังไม่มีใครทำดีจริง

## Real-world usage

**Scenario:** Dev บอก AI "add password reset flow"

| Without Knowai                              | With Knowai                                                                |
| -------------------------------------------- | --------------------------------------------------------------------------- |
| AI grep "password" → เขียน reset module ใหม่ | AI call `analyze_intent("add password reset flow")`                         |
| ลืม rate limit                               | ได้ cognition pack `auth` → token expiry, single-use, rate limit, audit log |
| ใช้ raw fetch                                | ได้ conventions → ใช้ TanStack Query + generated client                     |
| ไม่รู้ว่ามี `EmailTemplate` component        | ได้ reusable assets → reuse existing                                        |
| ไม่รู้ว่าทีมเลือก email provider เจ้าไหน     | ได้ memory → "team uses SendGrid, fallback SES" (approved by team)          |

→ จาก "AI gen ผิด → human review 30 นาที" เหลือ "AI gen ถูก first try"
