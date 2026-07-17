# Request routing + Wayfinder — จากคำขอคลุมเครือสู่ flow ที่พร้อมออกแบบ

> เอกสารนี้กำหนดเส้นทางของ Sage สำหรับคำขอที่ชัด, คลุมเครือแต่จบได้ใน session
> เดียว และงานใหญ่เกินหนึ่ง session รวมถึง durable artifacts, domain glossary,
> ticket frontier และ handoff ไป `/sage-flow` อ้างอิง source จริง ณ 2026-07-17

## 1. Header + design decisions

Sage ต้อง route ก่อนเริ่มออกแบบ ไม่ใช่รอให้ `/sage-flow` รับ fog ทุกขนาด
Routing ใช้ความชัดของ decision และขนาด session ไม่ใช้จำนวนไฟล์อย่างเดียว:

- `clear-single-session` — intent, terminology และ scope ชัดพอให้ flow หรือ code
- `foggy-single-session` — มี genuine human decisions แต่คาดว่าปิดได้ใน session เดียว
- `large-multi-session` — destination ยังมี fog และการตัดสินใจ/วิจัยเกินหนึ่ง session

Design decisions:

- `/sage-grill` เป็น always-on routing guard สำหรับ fog ไม่ใช่ checklist item และ
  ไม่ขึ้นกับว่า `plan-flow` ถูกเลือกหรือไม่
- `/sage-wayfinder` เป็น command แยก เพราะมี persistent map, ticket lifecycle,
  blocking, claim และ multi-session handoff ซึ่งต่างจาก flow design
- Local Markdown เป็น default backend ที่ portable; issue tracker ใช้เมื่อ repo
  มี committed tracker instructions และ agent มีเครื่องมือที่เกี่ยวข้อง
- `agents/sage/<domain>/context.md` เป็น glossary เท่านั้น สร้าง lazily และอัปเดต
  ทันทีเมื่อ term ถูกตกลง ไม่เก็บ implementation detail หรือ decision rationale
- `/sage-flow` consume resolved product decisions; ถ้า code/schema ขัดกับ decision
  ให้ reopen decision โดยอ้างหลักฐานใหม่ ไม่ถามซ้ำโดยไม่มีเหตุ

**Out of scope**

- ไม่เพิ่ม checklist item ที่หก
- ไม่บังคับ issue tracker, GitHub, Linear หรือ network service
- ไม่สร้าง executable project-management service หรือ database
- ไม่ใช้ Wayfinder กับงานที่ทางเดินชัดและจบใน session เดียว
- ไม่ให้ agent ตอบ HITL decision แทน human
- ไม่ให้ Wayfinder ลงมือสร้าง destination; มันผลิต decisions และ handoff artifacts

## 2. Actors & Systems

| System | Responsibility | Ownership |
| --- | --- | --- |
| Human | ตอบ product/domain decisions และยืนยัน shared understanding | HITL decisions, scope, terminology |
| Sage router | จำแนก route และบังคับ exit contract | Route state ก่อน design/code |
| Sage Grill | ปิด product intent, terminology, scope และ trade-offs | Single-session decision tree + checkpoint spec |
| Sage Wayfinder | ทำแผนที่ fog ข้าม session และจัด frontier | Map/ticket lifecycle |
| Sage Flow | ออกแบบ implementation จาก requirements ที่ชัด | APIs, state, failures, security, build plan |
| Domain knowledge | เก็บ glossary, rules และ durable decisions | `context.md`, `rules.md`, `decisions/` |
| Local filesystem / issue tracker | เก็บ map และ tickets | Canonical state ของ wayfinding effort |

**Trust boundary:** facts จาก code/schema/docs ต้องถูกค้นเอง Human เป็น source ของ
product intent เท่านั้น HITL ticket ปิดได้จาก live answer ของ human; AFK ticket
ปิดได้จาก evidence Agent ห้ามถือ recommendation ของตัวเองเป็น human confirmation

## 3. End-to-end overview

```text
[User request]
   │
   ▼ Sage router: classify code/non-code + inspect enough facts to size the fog
   │
   ├─ clear-single-session
   │    └─ checklist → /sage-flow when selected → implementation
   │
   ├─ foggy-single-session
   │    └─ /sage-grill
   │         ├─ checkpoint spec when >1 decision / cross-session risk
   │         ├─ update domain context inline
   │         └─ requirements-clear → /sage-flow or implementation
   │
   └─ large-multi-session
        └─ /sage-wayfinder chart
             ├─ map destination + fog + out-of-scope
             ├─ create research/prototype/grilling/task tickets
             └─ work one frontier ticket per session
                    │
                    ├─ more fog → add/wire tickets
                    └─ map clear → synthesize spec → /sage-flow
```

**หัวใจ:** Grill resolves a decision tree; Wayfinder persists and coordinates a
decision graph; Flow designs the implementation. แต่ละขั้นมี artifact และ exit
condition ต่างกันจึงไม่ถามหรือเก็บคำตอบซ้ำ

## 4. Step-by-step

### STEP 1 — Route the request

**System:** Sage router

- ตรวจว่าคำขอมี unresolved product decision ที่เปลี่ยน user behavior, scope,
  terminology, data ownership หรือ trade-off หรือไม่
- ตรวจว่า fog เหลือมากกว่าหนึ่ง session หรือมี independent research/prototype/
  decision branches ที่ต้อง coordinate หรือไม่
- `clear-single-session` เมื่อ implementation path อาจซับซ้อนแต่ product decision ชัด
- `foggy-single-session` เมื่อ decision tree สามารถเดินทีละคำถามใน session เดียว
- `large-multi-session` เมื่อยังเขียน complete flow โดยไม่เดาไม่ได้และ route เกิน
  session เดียว
- Reclassify เมื่อ research พบ fog หรือ when no-fog early exit proves work smaller

### STEP 2 — Grill a single-session request

**System:** Sage Grill + Human + Repository

- โหลด role, domain index/rules/decisions และ `context.md` เมื่อมี
- ค้น facts จาก code/schema/docs เอง
- ถาม most-blocking genuine decision ทีละข้อ พร้อม recommendation
- ก่อนปิด material decision ให้ทดสอบ concrete boundary/counterexample อย่างน้อย
  หนึ่งกรณี เช่น retry, partial failure, permission mismatch หรือศัพท์ชนกัน
- เมื่อ statement ของ human ขัดกับ code ให้แสดง contradiction เป็น fact + decision
  ไม่แก้คำตอบให้เข้ากับ code อย่างเงียบ ๆ
- เมื่อ term นิ่งให้อัปเดต `context.md` ทันที

### STEP 3 — Checkpoint Grill state

**System:** Sage Grill + local filesystem

- ถ้ามี open decisions มากกว่าหนึ่ง, เสี่ยงข้าม session หรือ user ต้องการ artifact
  ให้สร้าง `agents/sage/flows/<slug>-spec.md` **ก่อนคำถามแรก**
- หลังทุก human answer ให้ update `Decided`, `Still open`, `Out of scope`,
  `Terms changed`, `Last updated`
- Decision detail อยู่ใน spec ครั้งเดียว; summary link ไป spec ไม่ copy rationale
- Single small decision ใช้ chat-only ได้และเขียน spec ตอนจบเมื่อควรอยู่ข้าม chat

### STEP 4 — Exit Grill without duplicate questions

**System:** Sage Grill → Sage Flow

Grill exit state `requirements-clear` ต้องมี:

- product intent และ success outcome
- canonical terms ที่ใช้ใน request
- scope/out-of-scope
- resolved product trade-offs
- ไม่มี open HITL decision ที่เปลี่ยน implementation shape

Flow รับ spec เป็น source of truth และ grill เฉพาะ design uncertainty ที่ค้นพบจาก
code/schema หากหลักฐานใหม่ขัด decision เดิมให้ reopen โดยชื่อ decision + evidence

### STEP 5 — Chart a Wayfinder map

**System:** Sage Wayfinder + Human + storage backend

- Grill destination ก่อน: spec, approved decision หรือ implementation-ready change
- Grill breadth-first เพื่อหา frontier; ถ้าไม่มี fog ให้ early exit ไป Grill/Flow
- Local backend: สร้าง `agents/sage/wayfinders/<slug>/map.md` และ `tickets/*.md`
- Tracker backend: ใช้ committed tracker instructions, native child/blocking/
  assignment เมื่อมี; fallback local เมื่อไม่มี
- Map เป็น index: เก็บ destination, notes, linked decision gists,
  `Not yet specified`, `Out of scope`, ticket index; full answer อยู่ ticket เดียว
- Create tickets ก่อน แล้ว wire `blocked_by` รอบสองเมื่อ ids พร้อม

### STEP 6 — Work the frontier

**System:** Sage Wayfinder session

- โหลด map low-resolution ไม่อ่านทุก ticket
- เลือก first open, unblocked, unclaimed ticket หรือ ticket ที่ user ระบุ
- Re-read canonical state แล้ว claim ก่อน work
- หนึ่ง session ปิดไม่เกินหนึ่ง non-research ticket
- `research` เป็น AFK; `prototype` และ `grilling` เป็น HITL; `task` เป็น HITL/AFK
- บันทึก resolution ใน ticket, close, แล้วเพิ่ม one-line gist + link ที่ map
- เพิ่ม/wire newly visible tickets และลบ fog patch ที่ graduate แล้ว
- Ticket ที่พ้น destination → close เป็น out-of-scope ไม่เพิ่มใน decisions-so-far

### STEP 7 — Complete Wayfinder and hand off

**System:** Sage Wayfinder → Sage Flow

Complete เมื่อ:

- ไม่มี open tickets
- `Not yet specified` ว่าง
- destination ยังตรงกับ scope ปัจจุบัน
- decisions-so-far link ไป source ticket ครบ

จากนั้น synthesize `agents/sage/flows/<slug>-spec.md` โดยไม่ re-interview และส่ง
ไป `/sage-flow` `/sage-flow` ห้ามเริ่มจาก map ที่ยังไม่ complete

## 5. State / data handling

| State | Canonical location | Lifecycle |
| --- | --- | --- |
| Route | current Sage run | classify ก่อน design; reassess เมื่อ fog/size เปลี่ยน |
| Domain terms | `agents/sage/<domain>/context.md` | create lazily; update immediately after agreement |
| Grill checkpoint | `agents/sage/flows/<slug>-spec.md` | create before first question when checkpoint criteria match; update each answer |
| Wayfinder map | local `map.md` or configured tracker map | one canonical backend per effort |
| Wayfinder ticket | local `tickets/<id>.md` or tracker child issue | open → claimed → closed/out-of-scope |
| Flow | `agents/sage/flows/<slug>-flow.md` | created only from clear requirements |

Local map frontmatter/fields:

```yaml
id: <slug>
status: charting | active | complete
backend: local-markdown
updated: <ISO-8601>
```

Local ticket frontmatter/fields:

```yaml
id: <stable-slug>
title: <human-readable name>
type: research | prototype | grilling | task
mode: HITL | AFK
status: open | claimed | closed | out-of-scope
assignee: ""
blocked_by: []
updated: <ISO-8601>
```

## 6. API spec — N/A

ไม่มี network API ใหม่ Tracker backend ใช้ capability ที่ repo กำหนดไว้และไม่เป็น
dependency ของ Sage Local Markdown schema ข้างต้นคือ public artifact contract

## 7. Status lifecycle

```text
ROUTE_UNASSESSED
  ├─ CLEAR_SINGLE_SESSION → FLOW_OR_BUILD
  ├─ FOGGY_SINGLE_SESSION → GRILLING → REQUIREMENTS_CLEAR
  └─ LARGE_MULTI_SESSION  → CHARTING → ACTIVE_MAP
                                      │
                                      ├─ TICKET_OPEN → CLAIMED → CLOSED
                                      ├─ TICKET_OPEN → OUT_OF_SCOPE
                                      └─ NO_TICKETS + NO_FOG → MAP_COMPLETE

REQUIREMENTS_CLEAR | MAP_COMPLETE → SPEC_READY → FLOW_DESIGN → IMPLEMENTATION
```

Illegal transitions:

- `HITL open → closed` โดยไม่มี human answer
- `blocked ticket → claimed`
- `unclaimed ticket → working` ใน multi-session map
- `active map → flow` ขณะที่มี open ticket หรือ fog
- resolved product decision → flow question ซ้ำโดยไม่มี new contradictory evidence

## 8. Edge cases & error handling

| Case | Handling |
| --- | --- |
| “แก้ typo” | route `clear-single-session`; ไม่ grill |
| “ทำ onboarding ให้ดีขึ้น” | route `foggy-single-session`; grill intent/success first |
| “สร้าง ERP หลาย repo” | route `large-multi-session`; chart Wayfinder |
| plan-flow ถูกปิดแต่ request foggy | grill/wayfinder guard ยังทำงาน; ห้าม code past fog |
| breadth-first pass พบ no fog | ไม่สร้าง map; early exit ไป Grill/Flow |
| human answer ขัด code | แสดง contradiction และถาม genuine decision; ห้ามเลือกเอง |
| session จบกลาง Grill | checkpoint spec มีคำตอบล่าสุดและ next open decision |
| two sessions claim same local ticket | re-read before claim; second session skips claimed ticket; report conflict if simultaneous write |
| blocker ถูก reopen | dependent ticket กลับ blocked; ห้าม claim |
| decision invalidates tickets | update/close invalid tickets and blocking edges before continuing |
| tracker unavailable | fallback local Markdown; do not block planning on external integration |
| term is implementation detail | ไม่เขียน context; เก็บใน spec/flow/decision ตามชนิด |

## 9. Security & concurrency

- Map/tickets ห้ามเก็บ secrets, credentials หรือ PII values; link ไป approved store
- Tracker writes เป็น external mutation ใช้เฉพาะเมื่อ user/repo วาง tracker ใน scope
- Local claim ไม่ atomic; re-read ก่อน claim และใช้ one-ticket-per-session ลด collision
- Native tracker assignment/blocking เป็น source of truth เมื่อ tracker backend active
- HITL ticket ห้าม agent impersonate human
- Research facts ต้องมี source pointer; recommendation ไม่ใช่ evidence

## 10. Build checklist

### Router and protocol

- [x] เพิ่ม three-route gate ใน `AGENTS.md` และ `/sage`
- [x] ทำ grill/wayfinder independent จาก `plan-flow`
- [x] ลบ `TodoWrite` decision-map path ออกจาก `/sage-flow`
- [x] กำหนด Grill/Flow exit contract

### Grill with docs

- [x] เพิ่ม `context.md` glossary format ใน knowledge tree
- [x] เพิ่ม inline term updates, code contradiction และ scenario challenge
- [x] เพิ่ม durable checkpoint spec before-first-question rule
- [x] เพิ่ม strict ADR gate สำหรับ Grill decisions

### Wayfinder

- [x] สร้าง canonical `/sage-wayfinder` command
- [x] เพิ่ม local map/ticket schemas, frontier, blocking, claim และ completion handoff
- [x] เพิ่ม optional tracker backend without hard dependency

### Distribution and proof

- [x] เพิ่ม adapters ทุก integration และ installer command lists
- [x] อัปเดต README, command index, user docs และ changelog
- [x] เพิ่ม routing/behavioral contract fixtures + tests
- [x] รัน full protocol tests, legacy scan และ diff audit

## 11. Open questions

ไม่มี — user อนุมัติ scope ทั้งชุด Local Markdown default รักษา portability และ
optional tracker backend ไม่สร้าง external mutation โดยอัตโนมัติ

## 12. Skeptical verification

- Routing ใช้ fog + session size ไม่ใช้ความเสี่ยงหรือจำนวนไฟล์แทนกัน
- `plan-flow` off ไม่เปิดช่อง code past unresolved product decision
- Glossary แยกจาก spec/ADR จึงไม่ปน implementation detail
- Checkpoint ก่อนคำถามแรกป้องกันคำตอบหายกลาง session
- Scenario challenge เกิดก่อนปิด material decision ไม่เพิ่ม friction ให้ trivial choice
- Local map มี ticket index เพราะไม่มี tracker query แต่ answer detail ยังอยู่ที่ ticket เดียว
- One-ticket-per-session และ claim rules ลด duplicate work โดยไม่อ้าง atomicity ที่ไม่มี
- Flow ไม่ถาม resolved product decision ซ้ำ เว้นแต่มี new contradictory evidence
- No-fog early exit ป้องกัน Wayfinder กลายเป็นพิธีกรรมสำหรับงานเล็ก

## 13. Open Questions after verification

ไม่มี — ready to implement
