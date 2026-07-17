# Request routing, Sage Grill และ Sage Wayfinder

> Sage เลือกวิธีทำงานจาก “decision fog ที่ยังเหลือ” ก่อนออกแบบหรือเขียนโค้ด
> งานชัดเดินหน้าได้ งานคลุมเครือใน session เดียวเข้า Grill และงานใหญ่ข้าม
> session เข้า Wayfinder อ้างอิง protocol จริง ณ 2026-07-17

## 1. Actors & Systems

| System | Responsibility | Ownership |
| --- | --- | --- |
| Human | ตอบ product/domain decisions และยืนยันศัพท์/scope | HITL decisions |
| Sage router | เลือกหนึ่งในสาม route | Route ก่อน design |
| Sage Grill | ปิด fog ที่จบได้ในหนึ่ง session | Requirements-clear handoff |
| Sage Wayfinder | จัด decision map/tickets ข้าม session | Persistent map + frontier |
| Sage Flow | ออกแบบ implementation จาก requirements ที่ชัด | Design-clear flow |
| Domain context | เก็บ canonical glossary | `agents/sage/<domain>/context.md` |

## 2. End-to-end overview

```text
[Request]
   │
   ▼ ตรวจ intent, terms, scope, trade-offs และ facts ที่หาได้จาก repo
   │
   ├─ clear-single-session
   │    └─ checklist → /sage-flow (เมื่อใช้) → implementation
   │
   ├─ foggy-single-session
   │    └─ /sage-grill → requirements-clear → /sage-flow
   │
   └─ large-multi-session
        └─ /sage-wayfinder
             ├─ Destination + tickets + blocking + frontier
             ├─ work one decision ticket/session
             └─ map complete → spec → /sage-flow
```

**หัวใจ:** routing guard เป็น core Sage ไม่ใช่ checklist item ปิด `plan-flow`
ไม่ได้แปลว่า agent สามารถเดา product decision แล้วเขียนโค้ดต่อได้

## 3. Three routes

### `clear-single-session`

ใช้เมื่อ intent, canonical terms, scope และ product trade-offs ชัดแล้ว แม้งาน
implementation จะใหญ่หรือหลายไฟล์ก็ยัง route นี้ได้ ถ้าไม่ต้องตัดสิน product
เพิ่ม

ตัวอย่าง:

- “แก้ typo ใน README”
- “Implement approved spec นี้; product decisions ปิดครบแล้ว”
- “ดูจาก schema ว่ามี `export_status` หรือไม่ แล้วเพิ่ม export ตาม contract” —
  schema เป็น fact ที่ agent ต้องค้นเอง ไม่ใช่คำถามถึง human

### `foggy-single-session`

ใช้เมื่อ genuine human decisions ยังเปลี่ยน outcome แต่คาดว่าถามทีละเรื่องแล้ว
จบได้ใน session เดียว

ตัวอย่าง: “ทำ onboarding ให้ดีขึ้น” ยังไม่บอกว่า success คือ completion rate,
time-to-value, tutorial UX หรือการลด support tickets จึงต้อง Grill ก่อน

### `large-multi-session`

ใช้เมื่อ Destination ยังมี research, prototype, grilling หรือ manual tasks เกิน
หนึ่ง session ไม่ได้ตัดสินจากจำนวนไฟล์อย่างเดียว

ตัวอย่าง: “สร้าง ERP ใหม่หลาย repo/หลายทีม” ต้อง chart domain boundaries,
source-of-truth, migration, integrations และ sequencing ก่อนสร้าง complete flow

## 4. Sage Grill — single-session fog with docs

Grill ทำห้าสิ่งตามลำดับ:

1. อ่าน domain glossary/rules/decisions และค้น code/schema facts เอง
2. สร้าง decision tree แล้วถาม most-blocking decision ทีละข้อ
3. แนะนำคำตอบ แต่ไม่ตอบ HITL decision แทน human
4. Stress-test material answer ด้วย concrete scenario/counterexample
5. อัปเดต glossary และ checkpoint ก่อนถามข้อต่อไป

### Durable checkpoint

เมื่อมีมากกว่าหนึ่ง decision, เสี่ยงข้าม session, หลายระบบพึ่งคำตอบ หรือ human
ต้องการ artifact Grill สร้าง
`agents/sage/flows/<slug>-spec.md` **ก่อนคำถามแรก** แล้วอัปเดตหลังทุกคำตอบ:

- Decisions
- Still open
- Out of scope
- Terms changed
- Evidence/source pointers
- Last updated

จึง resume ได้โดยไม่เริ่มสัมภาษณ์ใหม่เมื่อ context ถูกตัด

### Domain context

`agents/sage/<domain>/context.md` เก็บศัพท์เท่านั้น:

```markdown
## Customer

**Definition:** Legal/business party that owns the subscription.
**Invariants:** A subscription has one owning Customer even when many Users act
on its behalf.
**Includes:** A company or individual buyer.
**Excludes:** A login identity acting on the Customer's behalf.
**Related:** User, Subscription.
```

Term ถูก update ทันทีหลังตกลง Implementation details อยู่ใน spec/flow และ
hard-to-reverse trade-off อยู่ใน `decisions/` ไม่ปนใน glossary

### Exit contract

Grill ออกได้เมื่อ human ยืนยัน `requirements-clear`: intent, success outcome,
terms, scope/out-of-scope และ product trade-offs ปิดครบ Flow ห้ามถามซ้ำ เว้นแต่
พบ code/schema evidence ใหม่ที่ขัด decision เดิม และต้อง reopen โดยระบุชื่อ
decision กับหลักฐาน

## 5. Sage Wayfinder — persistent multi-session fog

Wayfinder มีสองโหมด:

### Chart

1. Grill `Destination`
2. สำรวจ breadth-first หา sharp questions และ fog
3. ถ้าไม่มี fog → early exit; ไม่สร้าง map
4. สร้าง map/tickets
5. Wire blocking หลัง ticket ids พร้อม
6. หยุดโดยไม่ hand-resolve ticket

### Work one ticket

1. โหลด map แบบ low-resolution
2. เลือก ticket จาก Frontier: open + unblocked + unclaimed
3. Claim ก่อน work
4. Resolve หนึ่ง non-research ticket ต่อ session
5. เก็บ full resolution ใน ticket
6. Map เก็บเพียง one-line gist + link
7. Graduate fog ที่ sharp แล้วเป็น tickets ใหม่

## 6. Local Markdown backend

หาก repo ไม่ได้ configure issue tracker, Sage ใช้:

```text
agents/sage/wayfinders/<slug>/
  map.md
  tickets/
    <ticket-id>.md
```

Map เก็บ `Destination`, `Decisions so far`, `Not yet specified`, `Out of scope`
และ ticket index Ticket เก็บ type/mode/status/assignee/blocked_by, Question,
Context, Resolution และ Assets

Issue tracker เป็น optional backend เท่านั้น ใช้เมื่อ repo มี committed
instructions, tool พร้อม และ external writes อยู่ใน scope ห้าม mirror state
ระหว่าง local กับ tracker

## 7. Ticket types

| Type | Mode | Purpose |
| --- | --- | --- |
| `research` | AFK | หาข้อเท็จจริงพร้อม source pointers |
| `prototype` | HITL | สร้าง artifact ราคาถูกให้ human ตอบสนอง |
| `grilling` | HITL | ปิด decision หนึ่ง branch ด้วย Grill discipline |
| `task` | HITL/AFK | manual work ที่ต้องเกิดเพื่อ unblock decision |

Ticket ไม่ใช่ implementation slice Wayfinder เสร็จเมื่อไม่มีอะไรต้องตัดสินใจ
ก่อนคนอื่นไป build Destination

## 8. State lifecycle

```text
route
  ├─ clear-single-session → flow/build
  ├─ foggy-single-session → grilling → requirements-clear
  └─ large-multi-session  → charting → active map
                                      ├─ open → claimed → closed
                                      └─ open → out-of-scope

no open tickets + no fog → map complete → spec-ready → flow
```

Invalid states:

- HITL ticket ปิดโดย agent โดยไม่มี human answer
- blocked ticket ถูก claim
- active/incomplete map ถูกส่งเข้า Flow
- Flow ถาม resolved product decision ซ้ำโดยไม่มี new evidence

## 9. Edge cases

| Case | Handling |
| --- | --- |
| `plan-flow` off แต่ request foggy | Grill/Wayfinder ยังทำงาน |
| Wayfinder chart พบ no fog | early exit ไม่สร้าง map |
| Human statement ขัด code | แสดง fact + ถาม decision; agent ห้ามเลือกเอง |
| Grill session ถูกตัด | resume จาก checkpoint spec |
| Local sessions claim ชนกัน | re-read ก่อน claim; second session ข้าม/report conflict |
| Decision ทำให้ ticket อื่น invalid | ปิด/update ticket และ dependency ก่อนต่อ |
| Tracker ใช้ไม่ได้ | fallback local Markdown |
| Term เป็น implementation detail | เก็บใน spec/flow ไม่ใส่ context |

## 10. Security & concurrency

- Maps/tickets ไม่เก็บ secrets หรือ PII values
- Tracker writes ต้องอยู่ใน user scope
- Local claim เป็น cooperative ไม่ใช่ atomic; ต้อง re-read ก่อน claim
- Research answer มี source pointer; recommendation ไม่ใช่ evidence
- HITL agent ห้าม impersonate human

## 11. Open questions

ไม่มีสำหรับ contract ปัจจุบัน Live model compliance eval ยังเป็น validation layer
แยกจาก static protocol tests
