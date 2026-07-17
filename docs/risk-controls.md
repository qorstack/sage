# Risk controls — Sage ใช้ความเสี่ยงเปลี่ยนวิธีทำงานอย่างไร

> Sage ประเมิน risk ก่อนเปลี่ยนไฟล์ บังคับ controls ตาม failure mode ที่พบ
> ตรวจหลักฐานจริงหลังลงมือ และรายงาน residual risk ก่อนปิดงาน เอกสารนี้อธิบาย
> behavior ของ protocol ณ 2026-07-17

## 1. Actors & Systems

| System | Responsibility | Ownership |
| --- | --- | --- |
| Human | กำหนด intent, scope และอนุมัติงาน HIGH/destructive | Product decision และ risk acceptance |
| Sage | ตรวจ drivers, ประเมิน level, บังคับ controls และ verdict | Risk assessment ของ run |
| Repository | ให้ code, schema, rules, history และ tests | Implementation facts |
| Specialist commands | ให้ flow/test/E2E/security evidence เมื่อ applicable | Evidence เฉพาะด้าน |

Sage ไม่ถือว่า `mode:auto` หรือคำสั่ง “ทำต่อได้เลย” เป็นการอนุมัติ target ที่
destructive หรือ HIGH โดยอัตโนมัติ Approval ต้องผูกกับ target และ effect ที่เปิดเผย

## 2. End-to-end overview

```text
[Coding request]
   │
   ▼ ตรวจ code/schema/rules และหา concrete risk drivers
[Initial assessment]
   │  Impact · Likelihood · Reversibility · Exposure · Confidence
   │
   ├─ LOW    → proceed เมื่อขอบเขตชัดและ controls พร้อม
   ├─ MEDIUM → warn หรือ ask ตาม reversibility/unknowns
   └─ HIGH   → ask ก่อนเปลี่ยนไฟล์
   │
   ▼ driver → required control → planned evidence
[Implementation]
   │
   ▼ run tests/build/lint + driver-specific controls
[Evidence]
   │
   ├─ missing/failed → stop, warn, ask หรือ reject
   └─ passed         → reassess
   │
[Summary] initial risk → controls/evidence → residual risk
```

**หัวใจ:** Risk level เลือก gate แต่ risk driver เลือกมาตรการ `HIGH` migration
และ `HIGH` authorization จึงไม่ถูกตรวจด้วย checklist เดียวกันแบบเหมารวม

## 3. Step-by-step

### STEP 1 — ตรวจ drivers จากของจริง

**System:** Sage + Repository

Sage อ่าน source, schema, contracts, rules และ history ก่อนประเมิน โดยมองหา:

- destructive/data loss
- schema/data migration
- auth/authorization/trust boundary
- money/payment
- PII/secrets
- public API/config/CLI contract
- production infrastructure
- concurrency/retry/external side effects
- dependency/supply chain
- validation gap หรือ important unknown

Driver ต้องระบุ asset และ failure mode เช่น `orders table → rows may be lost on
rollback` ไม่ใช่เพียง “database change is risky”

### STEP 2 — ประเมิน level และ confidence

**System:** Sage

- `Impact` — หากผิดจะเสียหายอะไร
- `Likelihood` — change path ทำให้เกิดได้อย่างไร
- `Reversibility` — rollback ได้เร็วและครบหรือไม่
- `Exposure` — กระทบ local, team, users, consumers หรือ production
- `Confidence` — มีหลักฐานอะไรและยังไม่รู้อะไร

Unknown ที่อาจซ่อน HIGH impact จะไม่ถูกเดาเป็น LOW แต่ถูกเปิดเผยเป็น driver และ
ทำให้ Sage ใช้ `ask` เมื่อจำเป็น

### STEP 3 — เลือก verdict

**System:** Sage + Human เมื่อจำเป็น

- `LOW / proceed` — งานมีขอบเขตชัดและ validation พร้อม
- `MEDIUM / warn` — งาน reversible และ controls ตรวจได้ครบ
- `MEDIUM / ask` — scope, contract, rollback หรือ unknown ต้องตัดสินใจ
- `HIGH / ask` — หยุดก่อนเปลี่ยนไฟล์และขอ explicit approval
- `reject` — ขัด `block` rule, unsafe หรือไม่มี bounded control ที่เพียงพอ

### STEP 4 — สร้าง control plan

**System:** Sage dispatcher

| Driver | Required evidence |
| --- | --- |
| Data loss | exact targets, backup/recovery, dry-run, explicit approval |
| Migration | migration history, backup, dry-run, rollback/forward-fix, integrity check |
| Authorization | ownership/IDOR checks, negative permission tests, token/session review |
| Payment | idempotency, atomicity, trusted amount, retry/reconciliation tests |
| PII/secrets | logging/exposure review, least privilege, redaction, available secret scan |
| Public contract | consumer search, compatibility test, version/rollout plan |
| Production infra | plan/diff, staged rollout, health check, rollback, monitoring |
| Retry/external effect | duplicate/retry test, race analysis, idempotency/locking |
| Dependency | official advisory/changelog, lockfile diff, compatibility/build tests |

Checklist ยังคงเลือก `/sage-flow`, unit, E2E และ security review ตาม applicability
แต่ required control เป็น core guard การปิด specialist ที่ไม่เกี่ยวข้องไม่ลบ control

### STEP 5 — ตรวจและประเมิน residual risk

**System:** QA + Sage

Sage รันคำสั่งจริงและผูก output กับแต่ละ control หาก control รันไม่ได้จะรายงาน
missing evidence และ consequence ไม่ถือว่าผ่าน จากนั้นจึงประเมิน residual risk:

- ลด level ได้เมื่อ evidence ลด likelihood/exposure หรือเพิ่ม reversibility
- control สำคัญล้มเหลวหรือ residual HIGH → ห้ามสรุปว่างานเสร็จอย่างปลอดภัย
- scope/driver ใหม่ระหว่างทำ → หยุด phase ที่กระทบและประเมินใหม่

## 4. State lifecycle

```text
UNASSESSED
  → ASSESSED(level + confidence + drivers)
  → APPROVED | WARNED | REJECTED
  → CONTROLS_RUNNING
  → VALIDATED | CONTROL_GAP
  → CLOSED(residual risk) | NEEDS_DECISION | REJECTED
```

Initial risk ไม่ถูก overwrite ด้วย residual risk เพื่อให้เห็นว่ามาตรการใดทำให้
ความเสี่ยงลดลงจริง

## 5. ตัวอย่าง

### Schema migration

```text
Risk: HIGH · confidence:high — migration rewrites production customer rows
Drivers: schema/data migration → partial rewrite may corrupt customer status
Required controls: backup + dry-run + rollback + post-migration integrity query
Decision: ask
```

หลังได้รับ explicit approval และ validation:

```text
Initial risk: HIGH
Validated: dry-run 50,000 rows passed; rollback restored checksum; integrity query 0 invalid
Residual risk: MEDIUM — staging volume is smaller than production; staged rollout remains
```

### Authorization change

```text
Risk: HIGH · confidence:medium — endpoint ownership behavior changes
Drivers: auth/authorization → user A may read user B's invoice
Required controls: IDOR review + negative permission integration test
Decision: ask
```

Security review เป็น specialist ที่เกี่ยวข้องในกรณีนี้ แต่ไม่ใช่ requirement ของ
HIGH migration ที่ไม่มี security boundary

## 6. Edge cases

| Case | Handling |
| --- | --- |
| User เลือก `mode:auto` | ข้าม checklist confirmation เท่านั้น; HIGH ยังหยุด |
| User ขอ autonomous execution | ไม่ครอบคลุม unnamed destructive target/effect |
| พบ driver ใหม่ระหว่างทำ | หยุด phase, reassess, เพิ่ม controls, renew approval เมื่อ scope เปลี่ยน |
| Tool สำหรับ control ไม่มี | รายงาน missing evidence และคง/เพิ่ม residual risk |
| Test suite ผ่านแต่ไม่ได้ทดสอบ driver | ไม่ถือเป็น driver-specific evidence |
| `block` rule ถูกละเมิด | `reject` หรือขอ explicit override ตาม rule; mode/checklist ไม่มีสิทธิ์ลด |

## 7. Security & concurrency

- Risk report ระบุ category/path แต่ไม่แสดง secret หรือ PII value
- Parallel validation รวม evidence ให้ครบก่อนประเมิน residual risk
- Critical control failure หยุด dependent phases
- Approval ผูกกับ scope, target และ disclosed effect เท่านั้น

## 8. Open questions

ไม่มีสำหรับ protocol ปัจจุบัน Numerical scoring, runtime risk service และการเพิ่ม
checklist item ใหม่อยู่นอกขอบเขตโดยตั้งใจ
