# /sage-security-review — review a change for real, exploitable security holes

Review a change (a diff, an endpoint, a flow, a module) for security defects that
an attacker could actually use — and report each with its concrete
attack path, not a generic checklist. Favour **few, real, high-confidence
findings** over a long list of theoretical ones.

**Stack-agnostic.** It reasons about the vulnerability classes that apply to what
the code does (web, API, data, auth, payments, infra), on any language or
framework. It reads the real code — it never guesses from names.

> **Invoked by the run checklist.** When `security-review` is active (§0 of
> `AGENTS.md`), Sage runs this itself for sensitive changes — auth, payment, PII,
> secrets, file upload, deserialization, anything crossing a trust boundary. It
> auto-unchecks when the change touches nothing sensitive (and says so).

---

## Model & effort — read the session ceiling first

Same discipline as `/sage`: detect the session **model + effort** and never
exceed either. Security reasoning is ceiling-level work — do not under-think it —
but never raise above the session level. State the ceiling once in the intent
block.

---

## Step 1 — Load role (`security`)

Open `agents/sage/roles/role-security.md` → adopt (create if missing; persona:
thinks like an attacker, assumes all input is hostile, traces data from untrusted
source to dangerous sink, cares about auth/authz/idempotency/secrets over style).
Output `Role: security [loaded|created]`.

> **Multi-repo:** anchor knowledge to the repo that owns the code under review.
> State it once in the intent block.

---

## Step 2 — Scope the change + the trust boundary

1. **Get the diff/target** — what changed, or the endpoint/flow to review. Read
   the real code and the data it handles. Prefer an existing
   `agents/sage/flows/<slug>-flow.md` for the intended trust boundary.
2. **Map untrusted input → dangerous sink.** For every entry point (request body,
   query, header, upload, webhook, message), trace where the data goes: a query,
   a shell/exec, a file path, a template, a redirect, a deserializer, an auth
   decision, a money computation.
3. **Read the domain rules.** If `agents/sage/<domain>/rules.md` or `decisions/`
   set security rules (idempotency required, ledger-only money, etc.), quote the
   ones that apply — a `block` rule here is non-negotiable.

---

## Step 3 — Review against the classes that apply

Consider only what the change actually does — don't force irrelevant categories:

- **AuthN / AuthZ** — missing/incorrect auth, IDOR (can user A act on user B's
  object?), privilege escalation, trusting a client-supplied id/role.
- **Injection** — SQL/NoSQL, command, path traversal, SSRF, template, header/CRLF.
- **Untrusted output** — XSS, unsafe deserialization, open redirect.
- **Secrets & crypto** — hardcoded secrets, secret in logs/response, weak/missing
  signature verification, predictable tokens.
- **Money & state** — missing idempotency (double charge), amount computed or
  trusted client-side, race condition on a state transition, missing atomicity.
- **Data exposure** — PII in logs/errors/responses, over-broad query, missing
  field-level authz.
- **Input validation & limits** — missing size/type/range checks, no rate limit
  on an expensive or abusable endpoint.
- **Config** — permissive CORS, debug on, verbose errors leaking internals.

Then output the intent block and wait for `proceed`/`ask`/`reject`:

```text
Repo    : <repo-root>
Role    : security — review of <target>
Model   : <model> @ effort:<effort>  ← session ceiling
Scope   : <files/endpoints/flow reviewed>
Sinks   : <untrusted-input → dangerous-sink paths found>
Risk    : LOW | MEDIUM | HIGH · confidence:<low|medium|high> — <why>
Drivers : <auth|money|PII|secrets|trust-boundary driver → failure mode>
Evidence: <parent required control → review/test/artifact>
Decision: proceed | ask | reject
```

---

## Step 4 — Verify each finding before reporting (no theatre)

For every candidate issue, confirm it's **real and reachable** before listing it:

- state the **concrete attack path**: input X at entry Y reaches sink Z → impact.
- confirm there is no existing guard upstream that already stops it (read the
  code — don't assume).
- rate **severity** (impact × exploitability) and **confidence**.
- drop anything you can't substantiate — a guessed vuln is noise. Prefer 3 real
  findings to 15 maybes.

---

## Step 5 — Report findings + fixes

For each confirmed finding: **what** (class), **where** (`file:line`), **attack
path** (how it's exploited), **impact**, **fix** (the minimal correct change,
matching the repo's patterns — reuse the existing validator/sanitizer/auth
helper, don't roll your own). If asked to fix, apply the fix and re-verify; if a
`block` domain rule is violated, the verdict is `reject` until it's resolved.

Return each confirmed finding to the parent run as a risk driver or an increase
in likelihood/exposure. Return each verified absence/guard as evidence for the
specific required control it covers. “No exploitable findings” is not evidence
for non-security controls such as migration rollback or public compatibility.

---

## Step 6 — Capture knowledge (mandatory)

- **A — New** security rule worth enforcing → `agents/sage/<domain>/decisions/<slug>.md`
  (pattern + why + Do/Avoid). Use `enforcement: block` for a must/never
  (idempotency on money, authz on every object fetch), `source: ai`,
  `status: proposed`.
- **B — Updated** an existing decision → update in place.
- **C — None** → `No new knowledge — <file> covers this`.

---

## Step 7 — Summary (mandatory — a response without this is incomplete)

Output as plain markdown (no code fence):

```markdown
── Sage Security Review ──────────────────────────
**Role** · security — review of <target>
**Model** · <model> @ effort:<effort>
**Scope** · <what was reviewed> | **Initial risk** · <LOW|MEDIUM|HIGH>

**Findings**
One block per confirmed finding: **[severity]** `<class>` at `<file:line>` —
attack path in one sentence → impact → the fix. "No exploitable findings" is a
valid, complete result — say it plainly when true.

**Verified**
How you confirmed each (traced input→sink; checked no upstream guard) — not
"looks insecure".

**Control evidence**
Map each parent-run security driver to the exact guard/test/finding, or state the gap.

**Residual risk** · <LOW|MEDIUM|HIGH> — <what the review evidence reduced or left open>

**Fixed** · [applied `<paths>` and re-verified | reported only, awaiting decision]

**Knowledge** · [new | updated | none] `<path>` — <rule title>
──────────────────────────────────────────────────
```

Then stop.
