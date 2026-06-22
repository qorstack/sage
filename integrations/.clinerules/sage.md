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
2. **A response without this block is incomplete.** Write in **full sentences**,
   not one-liners. Close with the block that matches your role:

   *Debugger / bug fix:*

   ```text
   ── Sage ──────────────────────────────────────────
   Role      : debugger — <task>
   Domain    : <domain>  |  Risk: <LOW|MEDIUM|HIGH>
   Root cause: <why it broke — name the exact function/variable/condition responsible>
   Mechanism : <how the failure propagated step by step to the visible symptom>
   Fix       : <what changed, why it addresses the root cause, any trade-offs>
   Validated : <concrete evidence — network tab, log output, test result. Not "looks correct">
   Slipped   : <why it wasn't caught — missing test, non-obvious API, wrong assumption>
   Knowledge : [new | updated | none] <path or reason>
   ──────────────────────────────────────────────────
   ```

   *Dev / build task:*

   ```text
   ── Sage ──────────────────────────────────────────
   Role      : <role> — <task>
   Domain    : <domain>  |  Risk: <LOW|MEDIUM|HIGH>
   Done      : <what was built or changed — sections, files, and their purpose>
   Decisions : <key choices and why — include alternatives considered and ruled out>
   Validated : <how you confirmed it works — what you ran, what the output looked like>
   Knowledge : [new | updated | none] <path or reason>
   ──────────────────────────────────────────────────
   ```

`AGENTS.md` is the source of truth — follow it verbatim.
