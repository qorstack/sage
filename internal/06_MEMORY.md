# 06 — Memory Layer

📂 [src/knowai/memory/](../src/knowai/memory/)

Persistent memory ข้าม session — สำหรับเก็บ business context, team decisions, approved conventions

## 2 backends

### FileMemoryStore (default)

- เก็บเป็น JSON ใน `.knowai/memory.json` ภายใน project
- keyword scoring search
- zero dependency
- เหมาะ solo dev / small team

### QdrantMemoryStore (optional)

- ใช้ `qdrant-client` + `sentence-transformers` (all-MiniLM-L6-v2)
- semantic search (เข้าใจ synonym)
- install: `uv sync --extra vector`
- fallback ไป FileMemoryStore อัตโนมัติถ้า Qdrant unreachable
- เหมาะ team ขนาดกลาง-ใหญ่ที่ memory เยอะ

## Memory types

| Type | ตัวอย่าง |
| --- | --- |
| `business_context` | "free tier limit = 1000 API calls/month — enforce at middleware layer" |
| `approved_convention` | "use SendGrid as primary email, SES as fallback" |
| `team_decision` | "deprecate Redis pub/sub, migrate to SQS by 2026-Q3" |
| `reusable_asset` | "Button component covers 95% of cases — don't create new variants" |
| `risk_pattern` | "deploying schema migrations during peak hours = incident" |
| `workflow` | "feature flag rollout: 5% → 25% → 100% over 1 week" |

## Human approval principle ⚠️ สำคัญ

```text
AI calls remember_business_context()
  → entry saved with approved=False
  → entry NOT injected into future analyses

Human runs: knowai memory approve <entry-id>
  → entry marked approved=True
  → entry NOW injected into analyze_intent reports
```

**ทำไม:** ป้องกัน AI ใส่ "ความรู้ผิด" เข้า system แล้วมั่วต่อไปเรื่อยๆ

ข้อยกเว้น: `remember_team_decision()` auto-approve (เพราะ human เป็นคนเรียก)

## API

```python
from knowai.memory import MemoryService

mem = MemoryService(repo_path="/path/to/repo")

# Save (AI flow)
entry_id = mem.save(
    type="business_context",
    domain="billing",
    title="Idempotency required",
    body="All payment mutations require idempotency-key header",
)

# Approve (human flow)
mem.approve(entry_id, approved_by="alice@company.com")

# Recall (during analyze_intent)
results = mem.recall(query="payment idempotency", domain="billing")
```

## Real-world usage

```bash
# Solo dev → save แล้ว approve เอง
uv run knowai memory decide billing \
  "Idempotency keys required" \
  --body "All payment API calls must include Idempotency-Key header to prevent duplicate charges from network retries"

# List
uv run knowai memory list --repo .

# Search
uv run knowai memory recall "rate limit"

# Delete
uv run knowai memory forget <entry-id>
```

**Scenario จริง:** Tech lead ตัดสินใจหลัง incident

1. เกิด incident: webhook handler ทำงานซ้ำเพราะไม่มี idempotency check
2. Lead post-mortem → ตัดสินใจ "ทุก webhook handler ต้องเช็ค event_id duplicate"
3. รัน `knowai memory decide webhook "Event ID idempotency" --body "..."`
4. สัปดาห์ต่อมา dev ใหม่ขอ AI เพิ่ม webhook handler
5. AI call `recall_context("webhook idempotency")` → ได้คำตอบทันที
6. AI gen code ถูก first try — ไม่ซ้ำ incident เดิม
