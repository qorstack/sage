# 07 — Reasoning Layer

📂 [src/knowai/reasoning/](../src/knowai/reasoning/)

**Rule-based pipeline ไม่ใช้ LLM** — deterministic, fast (<100ms), free

## Files

| File | Input → Output |
| --- | --- |
| `intent_analyzer.py` | request (str) → `IntentAnalysis` |
| `impact_analyzer.py` | `IntentAnalysis` → `ImpactAnalysis` |
| `risk_scorer.py` | intent + impact → `RiskAssessment` |
| `engine.py` | request → `CognitionReport` (รวมทุกอย่าง) |

## Pipeline

```text
"add rate limiting to /login"
   │
   ▼ IntentAnalyzer
   ├─ domain: auth              (keyword match)
   ├─ action: add               (verb)
   ├─ requirements: [token bucket / sliding window, audit log, retry-after header]
   └─ clarification_questions: ["per-user or per-IP?", "what limit?"]
   │
   ▼ ImpactAnalyzer
   ├─ affected_domains: [auth, audit, user]
   ├─ affected_services: [api-gateway, auth-service]
   ├─ affected_files: [8 files matched]
   └─ cascade_risks: ["legitimate user lockout", "shared proxy IP false positive"]
   │
   ▼ RiskScorer
   ├─ level: MEDIUM
   ├─ decision: WARN
   ├─ warnings: ["critical domain", "user-facing behavior change"]
   └─ workflow: [
       "1. Choose strategy (token bucket / sliding window)",
       "2. Add Redis or in-memory store",
       "3. Return 429 with Retry-After header",
       "4. Add audit log for blocked attempts",
       "5. Add metric for monitoring"
     ]
   │
   ▼ ReasoningEngine (combine everything)
   └─ CognitionReport
       ├─ intent, impact, risk
       ├─ plan
       ├─ reusable_assets       ← จาก Scanner
       ├─ conventions           ← จาก Scanner
       ├─ packs                 ← จาก Packs layer
       └─ memory                ← จาก Memory layer (approved only)
```

## Risk decisions

| Decision | ความหมาย | AI ทำอะไรต่อ |
| --- | --- | --- |
| `proceed` | ปลอดภัย, generate ได้เลย | เขียน code |
| `warn` | ต้องระวัง, แต่ผ่านได้ | เขียน code + แสดง warning |
| `ask` | ต้องถาม human ก่อน | submit approval queue, รอ approve |
| `reject` | ห้ามทำ | หยุด, อธิบายเหตุผล, propose alternative |

**Binding:** AI ห้ามข้าม `ask`/`reject` — Knowai ไม่มี LLM override กลไกนี้

## Risk scoring rules (current)

```text
+ critical domain (auth/billing/payments)    : +3
+ cross-repo impact                          : +2
+ touches forbidden patterns                 : +2
+ DB schema change                           : +2
+ public API change                          : +2
+ no existing tests in affected area         : +1
+ deploys outside maintenance window         : +1
─────────────────────────────────────────────
0-1  → proceed
2-3  → warn
4-5  → ask
6+   → reject
```

(Phase 4: เปลี่ยนเป็น ML-based scoring จาก historical incident data)

## Real-world usage

```bash
# CLI
uv run knowai analyze "add password reset" --repo /path/to/repo

# Output:
# Intent:
#   Domain: auth
#   Action: add
#   Inferred requirements:
#     - Reset token (single-use, time-limited)
#     - Email delivery
#     - Rate limiting (prevent enumeration)
#     - Audit log
#
# Impact:
#   Affected domains: auth, user, notification, audit
#   Affected services: auth-service, email-worker
#   Cascade risks: account enumeration, email bombing, token replay
#
# Risk: MEDIUM (4) → ASK
# Workflow:
#   1. Choose email provider (use approved memory: SendGrid)
#   2. Define token expiry (15 min typical)
#   3. Implement rate limit per email + per IP
#   4. Add audit logs
#   5. Integration test with email mock
```

**Scenario จริง:** Junior dev ขอ AI "fix login bug"

- AI call `analyze_intent("fix login bug")` → ได้ risk: HIGH, decision: ASK
- AI ตอบ junior: "ก่อนแก้ ขอถาม: bug เกิดที่ขั้นไหน? credential validation? session creation? token refresh?"
- Junior คิดจริงจัง → realize ตัวเองยังไม่รู้ scope
- ไม่มี code change มั่ว → ประหยัด review time
