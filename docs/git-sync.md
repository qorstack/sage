# 16 — Git Sync Setup (Step-by-step)

> เป้าหมาย: เปลี่ยน `~/.knowlyx/workspaces/x-product/` (local) ให้กลายเป็น **central knowledge ที่ทีมทุกคนใช้ร่วมกัน** ผ่าน git (GitHub / GitLab / self-host)
>
> ไม่ต้อง host server, ใช้ git auth ที่มีอยู่แล้ว

---

## ภาพรวม

```text
┌─────────────────────────────────────────────────┐
│  GitHub / GitLab repo                           │
│  github.com/company/x-product-knowledge.git     │
│                                                 │
│   workspace.toml                                │
│   memory.json                                   │
│   approvals.json                                │
│   packs/                                        │
└──────────────────┬──────────────────────────────┘
                   │ git push / pull
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   [Lead PC]   [Dev A PC]  [Dev B PC]
   ~/.knowlyx/workspaces/x-product/  (clone)
```

ทุกคนมี local clone ของ workspace, sync ผ่าน git

---

## Part 1 — Tech Lead: สร้างครั้งแรก

### Step 1 — สร้าง empty repo บน GitHub/GitLab

**GitHub:**

1. ไป https://github.com/new
2. Repository name: `x-product-knowledge`
3. Visibility: **Private** (ทุกคนในทีมเข้าได้, นอกทีมไม่เห็น)
4. **อย่า** tick "Add a README" — เริ่ม empty
5. Create repository
6. Copy URL: `git@github.com:company/x-product-knowledge.git`

**GitLab (cloud หรือ self-host):**

1. New project → Create blank project
2. Project name: `x-product-knowledge`
3. Visibility: **Private**
4. **Uncheck** "Initialize repository with a README"
5. Create project
6. Copy SSH URL

### Step 2 — สร้าง workspace local

```bash
knowlyx workspace create x-product
```

ผลลัพธ์: สร้าง `~/.knowlyx/workspaces/x-product/` พร้อม `workspace.toml`

### Step 3 — แก้ `workspace.toml` ใส่ repos + dependencies

```bash
# Mac/Linux
$EDITOR ~/.knowlyx/workspaces/x-product/workspace.toml

# Windows PowerShell
notepad $env:USERPROFILE\.knowlyx\workspaces\x-product\workspace.toml
```

ตัวอย่าง:

```toml
name = "x-product"
version = "1"
description = "Knowledge for X product"

[[repos]]
name = "x-website"
path = "../code/x-website"
role = "frontend"
domains = ["user", "checkout"]

[[repos]]
name = "x-service"
path = "../code/x-service"
role = "backend"
domains = ["user", "checkout", "billing"]
critical = true

[[dependencies]]
from = "x-website"
to = "x-service"
type = "api"
```

### Step 4 — Init git + push

```bash
cd ~/.knowlyx/workspaces/x-product

git init
git branch -M main

# เพิ่ม .gitignore (กัน cache โป๊ะ)
echo "scans/" > .gitignore
echo "*.tmp" >> .gitignore

git add .
git commit -m "init x-product workspace"

# ผูก remote (เปลี่ยน URL ตาม Step 1)
git remote add origin git@github.com:company/x-product-knowledge.git

git push -u origin main
```

✅ เสร็จ — central knowledge อยู่บน GitHub/GitLab แล้ว

### Step 5 — Link repo project ทั้งหมดของคุณ

ที่ machine ของ lead เอง, สำหรับทุก repo:

```bash
cd ~/code/x-website
knowlyx link x-product --role frontend --domains user,checkout
# → สร้าง .knowlyx/config.toml — commit ลง git ของ x-website

git add .knowlyx/config.toml
git commit -m "link to x-product knowlyx workspace"
git push
```

ทำซ้ำกับ `x-service`, `x-mobile`, ฯลฯ

---

## Part 2 — Dev คนอื่น: เริ่มใช้

### Step A — Clone workspace knowledge

```bash
# Mac/Linux
mkdir -p ~/.knowlyx/workspaces
git clone git@github.com:company/x-product-knowledge.git ~/.knowlyx/workspaces/x-product

# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.knowlyx\workspaces"
git clone git@github.com:company/x-product-knowledge.git "$env:USERPROFILE\.knowlyx\workspaces\x-product"
```

**สำคัญ:** path ต้องตรงเป๊ะ `~/.knowlyx/workspaces/<workspace-name>` — ไม่งั้น `knowlyx link` หาไม่เจอ

### Step B — Clone project repo ปกติ

```bash
git clone git@github.com:company/x-website.git
cd x-website
# .knowlyx/config.toml ติดมาจาก git แล้ว (Lead commit ไว้แล้ว)
```

### Step C — ใช้งานปกติ

```bash
knowlyx analyze "add checkout summary endpoint"
# → resolve workspace x-product อัตโนมัติ
# → อ่าน memory จาก ~/.knowlyx/workspaces/x-product/memory.json
# → AI เห็น decision ทุกอย่างที่ทีมเคยบันทึก
```

---

## Part 3 — Daily workflow

### ก่อนเริ่มงาน (pull latest)

```bash
cd ~/.knowlyx/workspaces/x-product
git pull
```

แนะนำตั้ง alias:

```bash
# .bashrc / .zshrc
alias kw-pull='cd ~/.knowlyx/workspaces/x-product && git pull && cd -'

# PowerShell profile
function kw-pull { Push-Location "$env:USERPROFILE\.knowlyx\workspaces\x-product"; git pull; Pop-Location }
```

### หลัง AI save memory / approval สำคัญ (push)

```bash
cd ~/.knowlyx/workspaces/x-product
git add memory.json approvals.json
git commit -m "decision: use react-query for all data fetching"
git push
```

แนะนำตั้ง alias:

```bash
alias kw-push='cd ~/.knowlyx/workspaces/x-product && git add -A && git commit -m "knowledge update" && git push && cd -'
```

---

## Part 4 — Self-hosted GitLab / Gitea / Forgejo

### URL ต่าง — ที่เหลือเหมือนกัน

```bash
git remote add origin git@git.company.internal:platform/x-product-knowledge.git
# หรือ HTTPS
git remote add origin https://git.company.internal/platform/x-product-knowledge.git
```

### Self-signed cert (HTTPS only)

```bash
# Permanent (เฉพาะ host นี้)
git config --global http."https://git.company.internal/".sslVerify false

# หรือใส่ CA cert
git config --global http."https://git.company.internal/".sslCAInfo /path/to/ca.crt
```

### Custom SSH port

```bash
# ~/.ssh/config
Host git.company.internal
  HostName git.company.internal
  User git
  Port 2222
  IdentityFile ~/.ssh/id_ed25519
```

จากนั้น URL เป็น `git@git.company.internal:platform/x-product-knowledge.git` ตามปกติ

---

## Part 5 — Auth

### ใช้ git auth ที่มีอยู่เลย — ไม่ต้อง Knowlyx token

| Method | Setup |
|---|---|
| SSH key | `ssh-keygen -t ed25519` → เพิ่ม public key ใน GitHub/GitLab settings |
| HTTPS + credential helper | `git config --global credential.helper store` (Linux) / `manager` (Win) / `osxkeychain` (Mac) |
| GitHub CLI | `gh auth login` |
| GitLab CLI | `glab auth login` |
| Personal Access Token (HTTPS) | ใช้แทน password เวลา prompt |

### ตรวจว่า auth ใช้ได้

```bash
ssh -T git@github.com
# Hi <username>! You've successfully authenticated...

# หรือ
git ls-remote git@github.com:company/x-product-knowledge.git
```

---

## Part 6 — Conflict resolution

### กรณีที่ 2 devs save memory พร้อมกัน

```bash
git pull
# CONFLICT (content): Merge conflict in memory.json
```

`memory.json` เป็น JSON object ที่ key คือ entry ID — เปิดดูจะเห็น 3 ส่วน:

```json
{
  "abc123": { "title": "decision A", ... },
<<<<<<< HEAD
  "def456": { "title": "decision B (yours)", ... }
=======
  "def456": { "title": "decision B (theirs)", ... }
>>>>>>> origin/main
}
```

วิธีที่ปลอดภัยที่สุด: **เก็บทั้งคู่** (รวม `created_at` ที่ใหม่กว่า):

```json
{
  "abc123": { "title": "decision A", ... },
  "def456": { "title": "decision B (theirs)", "created_at": "..." }
}
```

แล้ว:

```bash
git add memory.json
git commit
git push
```

> Phase 4.C (planned) จะมี `knowlyx sync pull --resolve auto` ที่ merge ให้อัตโนมัติ (timestamp-based, newer wins)

---

## Part 7 — Permissions

### GitHub

- Repo settings → Collaborators → invite team members
- ใช้ team-based permission (Settings → Manage access → Add teams)
- Optional: Branch protection rules บน `main` → require PR review สำหรับ memory changes สำคัญ

### GitLab

- Project → Members → Invite
- Roles:
  - **Developer** — pull + push (พอสำหรับ dev)
  - **Maintainer** — push direct ไป main + manage settings
- Protected branch สำหรับ `main`

---

## Part 8 — Verify ว่าทำงาน

```bash
# 1. ตรวจ workspace exist
knowlyx workspace list
# → x-product

# 2. ตรวจ link OK
cd ~/code/x-website
cat .knowlyx/config.toml
# workspace = "x-product"

# 3. Save memory test
knowlyx memory decide checkout \
  "Test sync" --body "ทดสอบว่า sync ใช้งานได้"

# 4. ดู git status ของ workspace
cd ~/.knowlyx/workspaces/x-product
git status
# → memory.json modified

git diff memory.json
# → เห็น entry ใหม่ที่เพิ่ม

git add memory.json
git commit -m "test: sync"
git push

# 5. ลองที่อีกเครื่อง (หรือลบ + clone ใหม่)
rm -rf ~/.knowlyx/workspaces/x-product
git clone git@github.com:company/x-product-knowledge.git ~/.knowlyx/workspaces/x-product

knowlyx memory list
# → เห็น "Test sync" ที่ save จากเครื่องแรก ✅
```

---

## Part 9 — Troubleshooting

| ปัญหา | สาเหตุ | แก้ |
|---|---|---|
| `knowlyx analyze` ไม่เจอ memory | `~/.knowlyx/workspaces/<name>/` ไม่มี | Clone จาก git ก่อน (Step A) |
| `Permission denied (publickey)` | SSH key ไม่ได้เพิ่มใน GitHub | `cat ~/.ssh/id_ed25519.pub` → paste ใน GitHub SSH keys |
| `fatal: remote origin already exists` | เคย add แล้ว | `git remote set-url origin <new-url>` |
| `memory.json conflict` ทุก pull | 2 คนแก้พร้อมกัน | ใช้ Part 6 resolve, ใช้ branch protection |
| Workspace path ผิด | clone ผิด folder | ต้องเป็น `~/.knowlyx/workspaces/<exact-workspace-name>` |
| Windows path เพี้ยน | ใช้ `~` ใน PowerShell ไม่ได้ | ใช้ `$env:USERPROFILE` แทน |

---

## Part 10 — Security checklist

- [ ] Repo เป็น **Private** (ไม่ใช่ Public)
- [ ] `memory.json` ไม่มี secrets / API keys / passwords (Knowlyx ไม่ควรเก็บอยู่แล้ว แต่ตรวจซ้ำ)
- [ ] `.gitignore` มี `scans/` (scan cache อาจมี path ที่เปิดเผยโครงสร้าง internal)
- [ ] Team access ใช้ least privilege (Developer พอ, ไม่ต้อง Admin)
- [ ] Branch protection บน `main` ถ้าทีมใหญ่
- [ ] Backup: GitHub/GitLab ก็คือ backup แล้ว แต่ถ้าอยากชัวร์ → mirror ไป second remote

---

## TL;DR

```bash
# Tech lead (ครั้งเดียว)
knowlyx workspace create x-product
cd ~/.knowlyx/workspaces/x-product
git init && git add . && git commit -m "init"
git remote add origin git@github.com:company/x-product-knowledge.git
git push -u origin main

# Dev คนอื่น (ครั้งเดียว)
git clone git@github.com:company/x-product-knowledge.git ~/.knowlyx/workspaces/x-product

# ทุกคน: ในแต่ละ project repo
cd ~/code/x-website
knowlyx link x-product --role frontend

# Daily
cd ~/.knowlyx/workspaces/x-product && git pull   # before
# ... AI works, save memory ...
git add . && git commit -m "..." && git push     # after
```

✅ ไม่ต้อง host server
✅ ใช้ git auth เดิม (SSH/HTTPS/CLI tool)
✅ Work กับ GitHub, GitLab cloud, self-hosted GitLab/Gitea/Forgejo
✅ Audit log มาฟรีจาก git history
✅ Permissions มาฟรีจาก repo access control
