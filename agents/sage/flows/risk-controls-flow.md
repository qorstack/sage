# Risk controls — จากการประเมินสู่มาตรการที่พิสูจน์ได้

> เอกสารนี้กำหนด behavior ของ Sage สำหรับ coding request ตั้งแต่ตรวจ risk
> drivers จนถึงตัดสิน verdict, บังคับ controls, เก็บ validation evidence และ
> ประเมิน residual risk ก่อนปิดงาน อ้างอิง protocol จริง ณ 2026-07-17

## 1. Header + design decisions

Risk ไม่ใช่เพียง `LOW | MEDIUM | HIGH` ใน reply header แต่เป็น state ที่ต้องมี
drivers, controls และ evidence รองรับ การเลือก specialist commands ใน checklist
ยังอิง task signals เพราะแต่ละ command มี applicability ต่างกัน แต่ required
controls อิง risk drivers โดยตรงและไม่สามารถปิดผ่าน checklist ได้

การตัดสินใจหลัก:

- `AGENTS.md` เป็น source of truth ของ risk policy; command อื่นอ้างถึง policy นี้
  และเพิ่มเฉพาะขั้นตอนเฉพาะ command
- `mode:auto` อนุญาตให้ข้าม checklist confirmation เท่านั้น ไม่อนุญาตให้ข้าม
  genuine human decision, matched `block` rule หรือ destructive `HIGH` risk
- Risk level เป็นผลจาก impact, likelihood, reversibility, exposure และ confidence
  แต่ controls ถูกเลือกจาก driver เพื่อไม่ให้มาตรการ generic
- Risk ก่อนลงมือและ residual risk หลัง validation เป็นคนละค่าและต้องรายงานทั้งคู่

**Out of scope**

- ไม่สร้าง numerical risk score หรืออ้างว่า probability แม่นยำ
- ไม่บังคับ `security-review` ให้กับ `HIGH` risk ทุกประเภท
- ไม่เพิ่ม checklist item ลำดับที่หก
- ไม่เพิ่ม runtime service, database หรือ dependency ให้ Sage
- ไม่เปลี่ยน knowledge governance หรือ flow/grill lifecycle นอกส่วนที่อ้าง risk

## 2. Actors & Systems

| System | Responsibility | Ownership |
| --- | --- | --- |
| Human | กำหนด intent, risk appetite และอนุมัติ decision ที่ย้อนกลับยาก | เป็นเจ้าของ product decision และ destructive approval |
| Sage dispatcher | ตรวจ signals, risk drivers, level และ verdict | เป็นเจ้าของ routing และ enforcement ก่อนเปลี่ยนไฟล์ |
| Specialist command | ทำ flow, tests, E2E หรือ security review เมื่อ applicable | เป็นเจ้าของหลักฐานเฉพาะด้าน |
| Repository | ให้ code, schema, rules, history และ test commands เป็น facts | เป็น source of truth ของ implementation |

**Trust boundary:** agent ห้ามลด risk เพื่อเดินหน้าสะดวก ห้ามถือว่า `mode:auto`
คือ destructive approval และห้ามถือข้อความว่า “autonomous” เป็น override ของ
matched `block` rule การอนุมัติของ human ครอบคลุมเฉพาะ scope และ risk ที่เปิดเผย
ใน intent block

## 3. End-to-end overview

```text
[Human] ส่ง coding request
   │
   ▼ Sage: classify request + inspect repo facts/rules
[Sage dispatcher] ตรวจ task signals และ risk drivers
   │
   ▼ ประเมิน Impact × Likelihood × Reversibility × Exposure + Confidence
   │
   ├─ LOW    → proceed เมื่อไม่มี block/unknown สำคัญ
   ├─ MEDIUM → warn หรือ ask ตาม decision/validation gap
   └─ HIGH   → ask; destructive/irreversible ต้อง explicit approval
   │
   ▼ สร้าง Required controls จาก driver (ไม่ใช่จาก label อย่างเดียว)
[Checklist] เลือก specialist commands ที่ applicable
   │
   ▼ Implement ภายใน approved scope
[Validation] รัน required controls + เก็บ command/output evidence
   │
   ├─ control fail/missing → stop, ask หรือ reject
   └─ controls pass        → ประเมิน residual risk
   │
[Summary] Initial risk → controls/evidence → residual risk → remaining action
```

**หัวใจ:** level ตัดสินความเข้มของ verdict แต่ driver ตัดสินว่าต้องทำอะไรเพื่อ
ลดความเสี่ยง และ evidence เป็นตัวพิสูจน์ว่ามาตรการเกิดขึ้นจริง

## 4. Step-by-step

### STEP 1 — Ground risk in repository facts

**System:** Sage dispatcher + Repository

- อ่าน scope จริง, diff target, schema, contracts, domain rules และ reusable assets
- แยก fact ที่ตรวจได้ออกจาก assumption
- เมื่อข้อมูลสำคัญขาด ให้เพิ่ม `unknown` driver และลด confidence; ห้ามเดาเป็น LOW

### STEP 2 — Identify risk drivers

**System:** Sage dispatcher

ตรวจอย่างน้อย drivers เหล่านี้เมื่อ applicable:

- destructive/data loss
- schema/data migration
- auth/authorization/trust boundary
- money/payment
- PII/secrets
- public API/config/CLI contract
- production infrastructure/deployment
- concurrency/retry/external side effects
- dependency/supply chain
- validation gap/unknown behavior

แต่ละ driver ระบุ affected asset และ concrete failure mode ไม่เขียนเพียง
“change is risky”

### STEP 3 — Assess level and confidence

**System:** Sage dispatcher

- `Impact`: ความเสียหายหากผิด
- `Likelihood`: โอกาสเกิดจาก change path ที่ตรวจพบ
- `Reversibility`: rollback ได้เร็วและครบหรือไม่
- `Exposure`: blast radius ถึง local, team, users หรือ production
- `Confidence`: หลักฐานเพียงพอแค่ไหน

Rules:

- เมื่อ impact สูงและย้อนกลับยาก → อย่างน้อย `HIGH`
- เมื่อมี unknown สำคัญที่อาจซ่อน HIGH impact → ห้ามต่ำกว่า `MEDIUM` และใช้ `ask`
- matched `block` violation → `reject` หรือ `ask` สำหรับ explicit override ตาม rule
- agent เพิ่มความเข้มได้เมื่อพบหลักฐานใหม่ แต่ลดไม่ได้โดยไม่มี evidence

### STEP 4 — Select verdict and controls

**System:** Sage dispatcher

- `LOW` → `proceed` เมื่อ controls พร้อมและไม่มี unresolved human decision
- `MEDIUM` → `warn` เมื่อ reversible และ validation ครบ; ใช้ `ask` เมื่อ scope,
  contract หรือ rollback ยังต้องตัดสินใจ
- `HIGH` → `ask` ก่อนเปลี่ยนไฟล์; destructive/irreversible action ต้องได้รับ
  explicit approval ที่ระบุ target
- `reject` → request ขัด block rule, unsafe หรือไม่สามารถควบคุมให้อยู่ในขอบเขตได้

สร้าง `Required controls` จากตารางใน §8 ก่อน implementation และผูกแต่ละ control
กับ validation command หรือ observable evidence

### STEP 5 — Execute within the approved envelope

**System:** Specialist commands + Sage implementation role

- checklist เปิด specialist command ตาม applicability ไม่ใช่ตาม level อย่างเดียว
- required controls เป็น core guard และยังอยู่แม้ user ปิด specialist ที่ไม่จำเป็น
- ถ้า scope หรือ driver เปลี่ยนระหว่างทำ ให้ประเมิน risk ใหม่ก่อนเดินหน้าต่อ
- approval เดิมใช้ไม่ได้กับ target หรือ destructive effect ที่เพิ่งค้นพบ

### STEP 6 — Validate controls

**System:** QA role + Repository

- รัน test/build/lint จริง
- รัน driver-specific controls ที่ประกาศไว้
- บันทึก command และผลจริง; ห้ามใช้ “should pass”
- control ที่ทำไม่ได้ต้องมีเหตุผล, consequence และเปลี่ยน residual risk/verdict

### STEP 7 — Compute residual risk and close

**System:** Sage dispatcher

- ประเมิน risk อีกครั้งจากผล validation
- ลด level ได้เฉพาะเมื่อ evidence ลด likelihood, exposure หรือเพิ่ม reversibility
- รายงาน `Initial risk`, `Controls`, `Evidence`, `Residual risk`
- residual `HIGH` หรือ control สำคัญล้มเหลว → ห้ามกล่าวว่างานเสร็จอย่างปลอดภัย;
  ใช้ `ask`, `warn` หรือ `reject` ตามสภาพจริง

## 5. State / data handling

| State | Created | Updated | Cleared |
| --- | --- | --- | --- |
| Task signals | หลัง classify request | เมื่อ scope เปลี่ยน | เมื่อจบ run |
| Risk drivers | ก่อน intent block | เมื่อพบ fact/driver ใหม่ | เก็บสรุปเฉพาะ run |
| Initial risk | ก่อนแก้ไฟล์ | ประเมินใหม่เมื่อ scope เปลี่ยน | ไม่ overwrite; ใช้เทียบ residual |
| Required controls | ก่อน implementation | เพิ่มเมื่อ driver ใหม่ปรากฏ | ปิดได้เมื่อมี evidence หรือ marked unavailable |
| Evidence | ระหว่าง validation | เมื่อ rerun | รายงานใน summary |
| Residual risk | หลัง validation | เมื่อ evidence เปลี่ยน | terminal state ของ run |

ไม่มี persistent runtime state เพิ่มเติม เอกสาร flow/summary และ knowledge decisions
เป็น artifact ที่อยู่ใน Git ตาม protocol เดิม

## 6. API spec — N/A

ไม่มี network API หรือ endpoint ใหม่ Contract ที่เปลี่ยนคือข้อความและ behavior ใน
`AGENTS.md` กับ `agents/sage/commands/*.md`

## 7. Status lifecycle

```text
UNASSESSED
  → ASSESSED(LOW|MEDIUM|HIGH, confidence)
  → APPROVED | WARNED | REJECTED
  → CONTROLS_RUNNING
  → VALIDATED | CONTROL_GAP
  → CLOSED(residual LOW|MEDIUM) | NEEDS_DECISION | REJECTED
```

- scope/driver เปลี่ยนเมื่อใด → กลับ `ASSESSED`
- `HIGH` ห้ามเปลี่ยนเป็น `APPROVED` ด้วย `mode:auto`
- `CONTROL_GAP` ห้ามเปลี่ยนเป็น `CLOSED` โดยไม่สะท้อน residual risk

## 8. Edge cases & mandatory controls

| Driver / case | Required controls |
| --- | --- |
| Destructive/data loss | resolve exact targets, backup/recovery path, dry-run when available, explicit approval |
| Schema/data migration | migration history, backup, dry-run, rollback/forward-fix, post-change integrity query |
| Auth/authorization | ownership/IDOR checks, negative permission tests, session/token boundary review |
| Money/payment | idempotency, atomicity, amount/source verification, retry/reconciliation tests |
| PII/secrets | exposure and logging review, least privilege, redaction, secret scan where available |
| Public contract | compatibility impact, consumer search, contract test, version/rollout plan |
| Production infra | plan/diff preview, staged rollout, health check, rollback, monitoring |
| Concurrency/external side effect | duplicate/retry test, race analysis, idempotency/locking, partial-failure handling |
| Dependency/supply chain | official changelog/advisory, lockfile diff, compatibility/build tests |
| Validation unavailable | state missing evidence, keep/increase residual risk, ask before risky completion |
| New driver discovered mid-run | stop affected phase, reassess, add controls, renew approval if envelope changed |
| User requests autonomous execution | may skip routine confirmation only; cannot bypass block rule or destructive HIGH approval |

## 9. Security & concurrency

- Risk text must not leak secret values or PII; name categories and paths only
- Parallel phases may validate independent controls แต่ summary ต้องรวม evidence จาก
  ทุก phase ก่อนคำนวณ residual risk
- Failure ใน control ที่เกี่ยวกับ correctness หยุด dependent phases ทันที
- Matched `block` rule outranks mode, checklist และ agent preference
- Approval must bind to scope, target and disclosed effect; vague prior approval is not
  authorization for newly discovered destructive work

## 10. Build checklist

### Protocol

- [x] เพิ่ม risk model, drivers, confidence และ required controls ใน `AGENTS.md`
- [x] ทำ stop/override semantics ให้มี source of truth เดียว
- [x] เพิ่ม initial/residual risk และ evidence ใน summary contract

### Commands

- [x] ให้ `/sage` อ้าง policy กลางและสร้าง control plan
- [x] ให้ `/sage-flow` แสดง risk drivers/controls ที่กระทบ design
- [x] ให้ `/sage-security-review` ส่ง findings กลับเป็น controls/evidence
- [x] ปรับ unit/E2E commands ให้รายงาน driver-specific evidence เมื่อ applicable

### Documentation and validation

- [x] อธิบาย behavior ใน README และ `docs/risk-controls.md` โดยไม่อ้าง numerical score
- [x] เพิ่ม static regression tests ป้องกัน HIGH/autonomous conflict และ field หาย
- [x] รัน tests และตรวจ diff ทั้งชุด

## 11. Open questions

ไม่มี — ผู้ใช้อนุมัติให้ปรับ risk lifecycle ทั้งชุด และ design นี้ไม่เพิ่ม external
service หรือ destructive repository operation

## 12. Skeptical verification

- `mode:auto` ถูกจำกัดไว้ที่ checklist confirmation ไม่ใช่ risk override
- HIGH security และ HIGH migration ได้ controls ต่างกัน จึงไม่ใช้ generic checklist
- MEDIUM ไม่หยุดทุกงานโดยไม่จำเป็น; reversible + validated สามารถ `warn` แล้วเดินหน้า
- residual risk ลดได้จาก evidence เท่านั้น จึงไม่ใช่การเปลี่ยน label เพื่อปิดงาน
- ไม่มี control ใดอ้าง tool ที่ทุก repo ต้องมี; unavailable control ถูกเปิดเผยและทำให้
  residual risk คงอยู่
- Flow ไม่มี API/storage side effect ที่ตกหล่น และทุก terminal path มี verdict ชัดเจน

## 13. Open Questions after verification

ไม่มี — ready to implement
