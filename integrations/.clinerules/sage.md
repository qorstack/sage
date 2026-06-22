# Sage

This project uses **Sage**. Before writing or modifying any code, read and
follow **`AGENTS.md`** at the repo root — the cognition protocol.

Every code change runs five steps. Steps 1–3 before code; steps 4–5 after.

**Before code:**

1. Pick the role lens for this phase (`architect`, `dev`, `debugger`, `frontend`,
   `qa`, …) — infer from the request. Roles hand off between phases: plan with
   `architect`, build with `dev`, fix with `debugger`. Each phase loads its own role.
   **Open `agents/sage/roles/role-<lens>.md` immediately.**
   - Found → read it, adopt as-is, output: `Role: <lens> [loaded]`. Do not re-derive.
   - Missing → write the file to disk now (before step 2), output: `Role: <lens> [created]`.
   On phase handoff output: `Role: <new-lens> [loaded] — handoff from <prev-lens>`.
   Never start a phase without outputting the role line.
2. Read `agents/sage/<domain>/rules.md` and relevant `decisions/` files.
   Quote the rules that apply. Find reusable assets — **open the source file
   and read its exports** before using them. Never infer an API from a name.
3. Output the intent block (Role · Intent · Touches · Risk · Decision), then
   declare a **parallel plan** — group tasks by phase, mark each `[parallel]` or
   `[sequential]`, assign effort `low / medium / high` (ceiling = current model;
   reduce to `low` for mechanical tasks to save tokens). Execute parallel phases
   in a single response. State `[parallel: A, B running]` at phase start.
   Stop and ask on `ask` / `reject`.

**After code:**

1. Capture knowledge — mandatory, every run. Knowledge goes to `agents/sage/`
   **in the repo**, never to local memory. Write the **pattern** (transferable
   rule), not the implementation. One of:
   `[new]` create `agents/sage/<domain>/decisions/<slug>.md` ·
   `[updated]` fix a stale entry ·
   `[none]` name the existing rule that covered this.
2. **A response without this block is incomplete.** Output as **plain markdown**
   (no code fence) the block that matches your role. Full sentences; bullet
   points for Mechanism, Fix, and Decisions.

   *Debugger / bug fix:*

   ```markdown
   ── Sage ──────────────────────────────────────────
   **Role** · debugger — <task>
   **Domain** · <domain> | **Risk** · <LOW|MEDIUM|HIGH>

   **Root cause**
   <why it broke — name the exact function/variable/condition responsible>

   **Mechanism**
   - <trigger>
   - <propagation>
   - <symptom>

   **Fix**
   - <what changed and why it addresses the root cause>
   - <trade-offs, if any>

   **Validated**
   <concrete evidence — network tab, log output, test result. Not "looks correct">

   **Slipped**
   <why it wasn't caught — missing test, non-obvious API, wrong assumption>

   **Knowledge** · [new | updated | none] `<path>` — <reason>
   ──────────────────────────────────────────────────
   ```

   *Dev / build task:*

   ```markdown
   ── Sage ──────────────────────────────────────────
   **Role** · <role> — <task>
   **Domain** · <domain> | **Risk** · <LOW|MEDIUM|HIGH>

   **Done**
   <what was built or changed — sections, files, and their purpose>

   **Decisions**
   - <key choice and why>
   - <alternatives considered and ruled out>

   **Validated**
   <how you confirmed it works — what you ran, what the output looked like>

   **Knowledge** · [new | updated | none] `<path>` — <reason>
   ──────────────────────────────────────────────────
   ```

`AGENTS.md` is the source of truth — follow it verbatim.
