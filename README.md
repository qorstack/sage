# knowai

**Cognitive enforcement layer for AI software development.**
**ชั้นบังคับให้ AI เข้าใจระบบก่อนเขียนโค้ด**

> Knowledge is passive. Cognition must be enforced.
> ความรู้เป็นแค่ข้อมูล — ต้องบังคับให้ AI เข้าใจก่อน

---

## English

### Step 1 — Install Docker

You need Docker + Docker Compose. That's it. No Python, no database setup.

Verify:

```bash
docker --version
docker compose version
```

### Step 2 — Clone and configure

```bash
git clone https://github.com/SatangBudsai/knowlyx.git knowai
cd knowai
cp .env.example .env
```

Default `.env` works for local use. For a team, edit `POSTGRES_PASSWORD` and `POSTGRES_HOST`.

### Step 3 — Start everything

```bash
docker compose up -d --build
```

This starts two services:
- **Postgres** on port `5432` — stores knowledge
- **Web dashboard** on port `8080` — team UI

Wait for both to be healthy:

```bash
docker compose ps
```

### Step 4 — Open the dashboard

Open in browser:

```
http://localhost:8080
```

You'll see the **Overview** page with all counts at 0.

### Step 5 — Add your first knowledge entry

Click **Knowledge** in the top nav, then:

1. Sign in with your name (sticky cookie, used for audit log)
2. Fill the form:
   - **Kind**: pick `team_decision`
   - **Domain**: e.g. `payment`
   - **Title**: e.g. `Use idempotency keys`
   - **Body**: e.g. `All POST /payments require an Idempotency-Key header.`
   - **Tags**: `payment, api`
   - Tick ☑ Auto-approve
3. Click **Save knowledge**

You'll land on the entry detail page. Go back to Overview — count is now 1.

### Step 6 — Install the CLI (for AI integration)

```bash
# Option A: uv (recommended)
uv tool install knowlyx

# Option B: pipx
pipx install knowlyx

# Option C: no install, run on demand
uvx knowai --version
```

Set the same env vars in your shell so CLI hits the same database:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=knowai
export POSTGRES_PASSWORD=knowai
export POSTGRES_DB=knowai
export POSTGRES_SCHEMA=public
```

### Step 7 — Connect to Claude Code

```bash
claude mcp add knowai -- uvx knowai mcp --repo .
claude mcp list      # should show: knowai ✓
```

Now when you chat with Claude, it automatically queries knowai before generating code.

### Step 7b — Or connect to Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "knowai": {
      "command": "uvx",
      "args": ["knowai", "mcp", "--repo", "."]
    }
  }
}
```

Restart Cursor.

### Step 8 — Test that it works

In your AI chat, type something like:
> "Add a refund endpoint to /payments"

The AI should call knowai's MCP tools and reply with:
- Existing reusable code
- Team decisions about payments (the entry from Step 5)
- Risk level + impact analysis

### Stop / restart / wipe

```bash
docker compose stop          # stop, keep data
docker compose start         # start again
docker compose down          # stop + remove containers (data kept in volume)
docker compose down -v       # also wipe all data
```

### Quick reference

| What you want | Where |
|---|---|
| See all knowledge | <http://localhost:8080/entries> |
| Add new knowledge | <http://localhost:8080/knowledge> |
| Audit log | <http://localhost:8080/audit> |
| Domain summaries | <http://localhost:8080/syntheses> |
| Health check | <http://localhost:8080/healthz> |
| Full test plan | [TEST_GUIDE.md](TEST_GUIDE.md) |

### Troubleshooting

| Problem | Fix |
|---|---|
| `docker compose up` fails | Make sure Docker Desktop is running |
| Web shows "unhealthy" | Wait 10s, Postgres is still booting. Check: `docker compose logs web` |
| Port 5432 / 8080 in use | Change `POSTGRES_PORT` / `WEB_PORT` in `.env` |
| Two similar entries instead of one merged | Embedding model failed to load. Check: `docker compose logs web | grep sentence` |
| AI doesn't see knowledge | Your shell env vars don't match `.env` |

---

## ภาษาไทย

### Step 1 — ติดตั้ง Docker

ต้องมี Docker + Docker Compose เท่านั้น ไม่ต้องลง Python, ไม่ต้องตั้งค่า database

ตรวจสอบ:

```bash
docker --version
docker compose version
```

### Step 2 — Clone และตั้งค่า

```bash
git clone https://github.com/SatangBudsai/knowlyx.git knowai
cd knowai
cp .env.example .env
```

ค่า default ใน `.env` ใช้สำหรับ local ได้เลย ถ้าใช้ทีมแก้ `POSTGRES_PASSWORD` กับ `POSTGRES_HOST`

### Step 3 — Start ทุกอย่าง

```bash
docker compose up -d --build
```

จะ start 2 services:
- **Postgres** port `5432` — เก็บ knowledge
- **Web dashboard** port `8080` — UI ของทีม

รอจน healthy ทั้งสอง:

```bash
docker compose ps
```

### Step 4 — เปิด dashboard

เปิด browser:

```
http://localhost:8080
```

จะเห็นหน้า **Overview** ค่าทั้งหมดเป็น 0

### Step 5 — เพิ่ม knowledge ตัวแรก

คลิก **Knowledge** ที่เมนูบน, แล้ว:

1. Sign in ด้วยชื่อตัวเอง (เก็บใน cookie, ใช้บันทึก audit log)
2. กรอกฟอร์ม:
   - **Kind**: เลือก `team_decision`
   - **Domain**: เช่น `payment`
   - **Title**: เช่น `Use idempotency keys`
   - **Body**: เช่น `ทุก POST /payments ต้องมี header Idempotency-Key`
   - **Tags**: `payment, api`
   - ติ๊ก ☑ Auto-approve
3. กด **Save knowledge**

จะไปหน้า entry detail. กลับไป Overview จะเห็นว่ามี 1 รายการแล้ว

### Step 6 — ติดตั้ง CLI (สำหรับเชื่อม AI)

```bash
# ทางเลือก A: uv (แนะนำ)
uv tool install knowlyx

# ทางเลือก B: pipx
pipx install knowlyx

# ทางเลือก C: ไม่ต้องติดตั้ง รันเป็นครั้งๆ
uvx knowai --version
```

ตั้ง env vars เดียวกันใน shell เพื่อให้ CLI เชื่อมต่อ database เดียวกัน:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=knowai
export POSTGRES_PASSWORD=knowai
export POSTGRES_DB=knowai
export POSTGRES_SCHEMA=public
```

### Step 7 — เชื่อมต่อ Claude Code

```bash
claude mcp add knowai -- uvx knowai mcp --repo .
claude mcp list      # ควรเห็น: knowai ✓
```

ทีนี้เวลา chat กับ Claude มันจะ query knowai อัตโนมัติก่อนเขียนโค้ด

### Step 7b — หรือเชื่อมต่อ Cursor

แก้ไฟล์ `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "knowai": {
      "command": "uvx",
      "args": ["knowai", "mcp", "--repo", "."]
    }
  }
}
```

Restart Cursor

### Step 8 — ทดสอบ

ใน AI chat ลองพิมพ์:
> "เพิ่ม refund endpoint ที่ /payments"

AI ควรเรียก MCP tools ของ knowai แล้วตอบกลับมาพร้อม:
- โค้ดเดิมที่ใช้ซ้ำได้
- การตัดสินใจของทีมเกี่ยวกับ payment (entry จาก Step 5)
- ระดับความเสี่ยง + impact analysis

### Stop / restart / ล้างข้อมูล

```bash
docker compose stop          # หยุด เก็บข้อมูลไว้
docker compose start         # เริ่มใหม่
docker compose down          # หยุด + ลบ container (ข้อมูลใน volume ยังอยู่)
docker compose down -v       # ลบข้อมูลทั้งหมด
```

### ดูข้อมูลที่ไหน

| ต้องการ | URL |
|---|---|
| ดู knowledge ทั้งหมด | <http://localhost:8080/entries> |
| เพิ่ม knowledge ใหม่ | <http://localhost:8080/knowledge> |
| ดู audit log | <http://localhost:8080/audit> |
| สรุปต่อ domain | <http://localhost:8080/syntheses> |
| Health check | <http://localhost:8080/healthz> |
| Test plan แบบเต็ม | [TEST_GUIDE.md](TEST_GUIDE.md) |

### แก้ปัญหา

| ปัญหา | วิธีแก้ |
|---|---|
| `docker compose up` ขึ้น error | ตรวจสอบว่า Docker Desktop รันอยู่ |
| Web ขึ้น "unhealthy" | รอ 10 วิ Postgres ยัง boot อยู่. ดู: `docker compose logs web` |
| Port 5432 / 8080 ชน | เปลี่ยน `POSTGRES_PORT` / `WEB_PORT` ใน `.env` |
| มี 2 entries คล้ายกันที่ควรจะ merge เป็น 1 | embedding model โหลดไม่สำเร็จ. ดู: `docker compose logs web | grep sentence` |
| AI ไม่เห็น knowledge | env vars ใน shell ไม่ตรงกับ `.env` |

---

## License

MIT — see [LICENSE](LICENSE).
