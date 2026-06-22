# Sage

This project uses **Sage**. Before writing or modifying any code, read and
follow **`AGENTS.md`** at the repo root — the cognition protocol.

Every code change runs five steps. Steps 1–3 before code; steps 4–5 after.

**Before code:**

1. Name the domain + action; pick the role lens (`dev`, `frontend`, `infra`, …).
   Load `agents/sage/roles/role-<lens>.md` or create it if missing.
2. Read `agents/sage/<domain>/rules.md` and relevant `decisions/` files.
   Quote the rules that apply. Find reusable assets — **open the source file
   and read its exports** before using them. Never infer an API from a name.
3. Output the intent block: Role · Intent · Touches · Risk · Decision · Plan.
   Stop and ask on `ask` / `reject`.

**After code:**

1. Capture knowledge — mandatory, every run. Knowledge goes to `agents/sage/`
   **in the repo**, never to local memory. Write the **pattern** (transferable
   rule), not the implementation. One of:
   `[new]` create `agents/sage/<domain>/decisions/<slug>.md` ·
   `[updated]` fix a stale entry ·
   `[none]` name the existing rule that covered this.
2. **A response without this block is incomplete.** Close with the block that
   matches your role:

   *Debugger / bug fix — write in full sentences, not one-liners:*

   ```text
   ── Sage ──────────────────────────────────────────
   Role      : debugger — <task>
   Domain    : <domain>  |  Risk: <LOW|MEDIUM|HIGH>
   Root cause: <why it broke — explain the specific condition or code path>
   Mechanism : <how the failure propagated step by step>
   Fix       : <what changed, why it addresses the root cause, any trade-offs>
   Validated : <concrete evidence the fix works — not "looks correct">
   Slipped   : <why this wasn't caught earlier — gap in tests, non-obvious API, etc.>
   Knowledge : [new | updated | none] <path or reason>
   ──────────────────────────────────────────────────
   ```

   *Dev / build task — write in full sentences, not one-liners:*

   ```text
   ── Sage ──────────────────────────────────────────
   Role      : <role> — <task>
   Domain    : <domain>  |  Risk: <LOW|MEDIUM|HIGH>
   Done      : <what was built or changed>
   Decisions : <key choices made and why — include trade-offs considered>
   Validated : <how you confirmed it works — what you ran or checked>
   Knowledge : [new | updated | none] <path or reason>
   ──────────────────────────────────────────────────
   ```

`AGENTS.md` is the source of truth — follow it verbatim.

---

## Sage Learning

When asked to "learn this codebase" or run sage-learning:

Study how **this team actually writes code** and turn it into Sage knowledge, so
every future agent writes code that matches them. Run once per repo, and again
after big refactors. Everything goes to `agents/sage/` **in the repo** — never
to local memory.

1. **Map the repo.** Identify domains, the stack, and conventions in use —
   naming, error handling, folder layout, logging, testing, repeated patterns.
2. **Find the reusable assets and read them — do not guess.** For each asset:
   - **Open the file and read its exports** — signatures, parameter shapes,
     return types. Never infer from the file name; only the source is authoritative.
   - Document the full API in `decisions/<slug>.md` (exported symbols + purpose).
   - Flag assets that cover more use-cases than their name suggests.
3. **Spot the rules-in-practice.** Each consistent pattern is a candidate rule.
4. **Write it to `agents/sage/`** (format in `AGENTS.md` §2):
   - per-domain `rules.md`; `decisions/<slug>.md`; update relevant role files.
   - Write the **pattern**, not the implementation — rules must apply next time.
5. **Diff before writing**: never duplicate an existing entry; update in place.

**A response without this block is incomplete.** Close with:

```text
── Sage Learning ─────────────────────────────────
Stack     : <language, framework, key libs>
Domains   : <list of domains found>
Written   :
  [new]     agents/sage/<domain>/decisions/<slug>.md — <pattern title>
  [updated] agents/sage/<domain>/rules.md — <what changed>
  [skipped] <file> — already covered by <existing-entry>
Next      : flip status: approved on entries you want enforced
──────────────────────────────────────────────────
```
