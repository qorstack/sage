# /sage — Sage cognition pipeline

Run before any non-trivial code change. Steps 1–3 run **before** you write code.
Steps 4–5 run **after**. All are mandatory — never skip, never abbreviate.

## Step 0 — Decide whether to ask, then run the checklist

**Guard (before anything): if the request changes no files — a pure question,
advice, or an explanation ("should we use pnpm?", "what does X do?") — it is NOT a
code request. Just answer it. Do NOT show the checklist in any mode**, and never
invent a "None / just answer" option to escape a picker you shouldn't have shown.

**Step 0a — read the per-machine preference.** Read `.sage-local.json` at the repo
root (gitignored). It holds `askMode` (`"always"` or `"smart"`) and the last
`checklist`.

- **First run — the file doesn't exist yet → ALWAYS show the checklist** (never
  skip the first time) **and ask how often to ask from now on.** Call
  **AskUserQuestion** with **two** questions: (1) the multi-select checklist below,
  and (2) single-select `"From now on, when should /sage ask this?"` → **Every
  time** (`askMode: "always"`) or **Only big changes** (`askMode: "smart"`, skips
  small one-liners like typos/renames; still pops up for anything that needs a
  plan). Then create `.sage-local.json` with `askMode` + `checklist`, and add it
  to `.gitignore` if missing.
- **`askMode: "always"`** → show the checklist on **every** run.
- **`askMode: "smart"`** → gauge the task: **substantial** (logic, control flow,
  API, schema, money/auth/PII, multiple files, a feature, a bug needing
  investigation) → show the checklist; **trivial** (typo, rename, log line,
  one-line edit, a question) → skip it with `Checklist · skipped (trivial: <why>)`
  and just do it (role + a glance at risk still apply; `automate-test` still runs).
  When unsure, treat it as substantial.
  - **Override:** if the task genuinely needs a plan — a feature, multi-file or
    cross-repo change, money/auth/PII, or real uncertainty — **always show the
    checklist and recommend `plan-flow`**, even in smart mode. Never let a
    plan-worthy task slip through as "trivial".

**Step 0b — the checklist (then MANDATORY).** When it's due, present it and get the
human's answer before proceeding — as mandatory as the language question in
`/sage-docs`: never skip it, never assume it, never code without it.

**How — use this EXACT picker, identical on every run and every machine. Do NOT
improvise it.** Call **AskUserQuestion**, `multiSelect: true`, header
`"Task: <task in one line>. Which /sage steps should run?"`. List **exactly these
five options, in this order, every time** — never add one (no "None", no
"just answer"), never drop one, never reorder or rename:

1. **auto-switch-model** — auto-pick model + effort per task, within the ceiling
2. **plan-flow** — design + verify the flow before coding (`/sage-flow`)
3. **unit-test** — write unit tests for the changed logic (`/sage-unit-test`)
4. **e2e-test** — drive the flow end-to-end, browser/load (`/sage-e2e-test`)
5. **security-review** — review sensitive changes for holes (`/sage-security-review`)

(The dialog appends its own "Other" — leave it; add no escapes of your own. A pure
question with no code never reaches here — it's trivial, so just answer it.)

**Pre-check honestly — the checked state MUST match the reason.** Check an option
only when it genuinely applies to THIS task; leave the rest **unchecked** with a
one-line reason. **Never check a step whose reason is "not applicable" or "only
if…"** — if it doesn't apply, it stays unchecked. Start from the saved `checklist`
in `.sage-local.json`; `auto-switch-model` defaults on unless the human pinned a
model.

`automate-test` (run the suite) and `update-docs` (`/sage-docs`) are **core** —
always run after code, never in the picker; just state that.

**Remember the last choice per machine.** Use the `checklist` from
`.sage-local.json` as the default checked/unchecked state, then adjust for this
task's obvious fit. **After the human answers, write their selection (and
`askMode`) back to `.sage-local.json`** — create the file and add it to
`.gitignore` if either is missing — so next time defaults to what they last chose
here. Shape (valid JSON; `askMode` is `"always"` or `"smart"`):

```json
{
  "askMode": "always",
  "checklist": {
    "auto-switch-model": true,
    "plan-flow": true,
    "unit-test": true,
    "e2e-test": false,
    "security-review": true
  }
}
```

**After they answer**, echo the confirmed line, then continue to the steps below,
invoking each selected command at its point in the pipeline:

```text
Checklist · ✓ plan-flow → /sage-flow · ✓ unit-test · ~~e2e-test~~ (no UI) · ~~security-review~~ (not sensitive) · ✓ auto-switch-model · core: automate-test + update-docs
```

If the environment has no way to prompt (a non-interactive/headless run), state
that, apply the recommended defaults (everything that fits the task), and say
which you enabled — never silently run nothing.

## Model & effort — applies to every step

### Detect the session ceiling — do this before every task

**Read the actual model and effort from the current session context.** Do not
recall from memory or assume from a previous run — the user may have changed
it. State what you detected at the top of Step 3.

The session ceiling is the **model version + effort level** the user has set
right now (e.g. `opus 4.8 @ effort:low`, `sonnet 4.6 @ effort:medium`). You must **never exceed either
dimension** on any sub-task, for any reason.

### Floor

**Default minimum is `sonnet @ low`.** Do not drop below `sonnet` — **except**
for the haiku whitelist below.

**`haiku @ low` is allowed (and preferred, to save tokens) for trivial,
mechanical, fully-specified tasks where no reasoning or judgment is needed:**

- Translation / rewording / fixing grammar or tone of existing text
- Adding a log/print line, a comment, or a TODO at a stated location
- A literal, explicitly-specified one-liner (rename a variable, change a
  constant, add an import the user named)
- Pure formatting / mechanical find-and-replace

**Do NOT use haiku** when the task needs any decision: logic, control flow,
API shape, error handling, schema, naming choices, or anything touching
behavior. When unsure whether a task qualifies → it does not; use `sonnet`.
Never exceed the session model (haiku is below sonnet, so it's always allowed
direction-wise — but only for the whitelist above).

### The session effort is both the default AND the hard ceiling

**The session effort is the cap. You may go BELOW it for trivial sub-tasks, but
NEVER above it — for any reason, no matter how complex the task.**

- If the session is `sonnet 4.6 @ effort:low` → **every** sub-task runs at
  `low`. A complex task does not get bumped to `medium` — it stays `low`.
- The only direction you may move is **down** (e.g. drop a one-line file read to
  `low` when the session is `medium`).
- "This task is standard implementation / complex logic" is **not** a reason to
  raise effort above the session level. The ceiling always wins.

### Effort levels — meaning only, NOT a target to pick

This table describes what each level _means_. It does **not** authorize raising
effort above the session ceiling. **Ignore every row above the session effort.**

| Effort   | What it means                                                     |
| -------- | ----------------------------------------------------------------- |
| `low`    | Simple edits, file reads, boilerplate — minimal reasoning needed  |
| `medium` | Standard implementation, moderate complexity                      |
| `high`   | Complex logic, architecture, root-cause, critical/risky decisions |
| `max`    | Hardest multi-system problems — only when `high` is not enough    |

### How to pick

1. Note the session effort — this is the default for every task **and** the cap.
2. For each sub-task, ask: is this trivial enough to run **below** the session
   effort? If yes, lower it. If no, leave it **at** the session effort.
3. Never raise above the session effort. If the session is `@ low`, the answer
   is always `low` — even for the hardest sub-task in the plan.
4. **Exception — never downgrade flow design.** `plan-flow` / `/sage-flow` always
   runs at the **full session model + effort** (the ceiling), never lowered — it
   is the highest-reasoning step. Lowering other trivial sub-tasks is fine; the
   flow build + verify is never one of them.
5. State the full version + effort for every task, e.g. `sonnet 4.6 @ effort:low`.

State the session effort once in the Step 3 intent block, then annotate each
task in the parallel plan with its own chosen tier (≤ session effort). Repeat in
the final summary.

> **Multi-repo workspace:** When multiple repos are open at once, anchor every
> path in this protocol (`AGENTS.md`, `agents/sage/`, role files) to the **repo
> root that owns the file you are editing** — find it by locating the closest
> ancestor directory that contains `AGENTS.md`. State it once in the Step 3
> intent block as `Repo: <repo-root>`. Never read knowledge from another repo
> and never write knowledge outside the active repo's `agents/sage/`.

---

## Step 1 — Load your role(s) (do this before reading the task)

Pick the lens the request calls for — not just `dev`. Infer it from the request:
`frontend`, `infra`, `security`, `qa`, `architect`, `designer`, `data`,
`writer` … any senior expert role applies.

**Roles can hand off between phases.** A single task may use more than one role
as work progresses — each phase uses the expert who owns that phase:

- `architect` → plan the approach
- `dev` → implement
- `debugger` → root-cause and fix
- `qa` → validate

When you enter a new phase, load that phase's role file and output the handoff:
`Role: dev [loaded] — handoff from architect`

**To load or create any role:** open `agents/sage/roles/role-<lens>.md`.

- **Found** → read it, adopt as-is. Output: `Role: <lens> [loaded]`
  Do not re-derive. Update the file at the end if this task adds something new.
- **Missing** → write it to disk now, before the next step. Use this format:

  ```markdown
  ---
  role: <lens>
  title: Senior <Lens>
  covers: [<domain>]
  updated: <today>
  ---

  ## Ikigai (who this role is)

  - Loves — …
  - Good at — … ← the role's expertise, stack, patterns, standards
  - Team needs — …
  - Worth it — …

  ## How I work

  - Reuse before writing; follow the domain's rules.md.
  - Name the blast radius; stop on HIGH risk.
  ```

  Then output: `Role: <lens> [created]`

Never start a phase without having output the role line for that phase.

---

## Step 2 — Read knowledge + find assets

1. Open `agents/sage/<domain>/rules.md` and any `decisions/` files whose title
   looks relevant. **Quote the rules that apply** — show the human you checked.
   If the domain folder is missing, note it and continue.

2. Search for reusable assets (utils, hooks, components, services). When you
   find one: **open the source file and read its exports**. Never infer an API
   from a name or decision description. Source is always authoritative.

---

## Step 3 — State intent + parallel plan before writing

Output this block, then wait for `ask`/`reject` before continuing.

```text
Repo    : <repo-root>  ← include only when multiple repos are open
Role    : <role> — <one-line task summary>
Model   : <model> @ effort:<effort>  ← ceiling = session model + session effort
Intent  : <what this change does>
Touches : <files, systems, domains affected>
Risk    : LOW | MEDIUM | HIGH — <why in one phrase>
Decision: proceed | warn | ask | reject
```

Then declare the **parallel plan**. Before listing tasks, identify which can run
at the same time (no dependency on each other) and which must be sequential.
Annotate each task with its tier — **every tier must be ≤ the session model and
≤ the session effort.** No task may exceed either.

The example below assumes a high session ceiling (e.g. `opus 4.8 @ effort:high`).
**If the session is `sonnet 4.6 @ effort:low`, every task must read
`sonnet effort: low` — including the complex ones. Never higher.**

```text
Plan  (session ceiling: opus 4.8 @ effort:high)
── Phase 1 [parallel] ─────────────────────────
  A. <task>                    sonnet  effort: low
  B. <task>                    haiku   effort: low
── Phase 2 [sequential] ───────────────────────
  C. <task — depends on A+B>   opus    effort: high
── Phase 3 [parallel] ─────────────────────────
  D. <task>                    sonnet  effort: medium
  E. <task>                    sonnet  effort: medium
```

Execute parallel phases in a single response (all their tool calls together).
Mark each task with 🟨 when it starts and ✅ when it completes. Each task
reports itself when IT finishes — do not wait for all to complete:

```text
── [phase 1 · parallel: A, B, C] ────────────────
  🟨 A [sonnet/low] — <brief what>
  … A tool calls …
  ✅ A — <one-line result>
  🟨 B [haiku/low] — <brief what>
  … B tool calls …
  ✅ B — <one-line result>
  🟨 C [sonnet/medium] — <brief what>
  … C tool calls …
  ✅ C — <one-line result>
── [phase 1 → all done, proceeding to phase 2] ──

── [phase 2 · sequential: D — depends on A, B] ──
  🟨 D [opus/high] — <brief what>
  … D tool calls …
  ✅ D — <one-line result>
── [phase 2 → done, proceeding to phase 3] ──────

── [phase 3 · parallel: E, F] ───────────────────
  🟨 E [sonnet/medium] — <brief what>
  … E tool calls …
  ✅ E — <one-line result>
  🟨 F [sonnet/medium] — <brief what>
  … F tool calls …
  ✅ F — <one-line result>
── [phase 3 → all done] ─────────────────────────
```

If a task fails, report it immediately and pause:
`❌ B — <reason>. Pausing — waiting for input before continuing.`
Never silently continue past a failure.

---

## [write the code]

---

## Step 4 — Capture knowledge (mandatory, every run)

Knowledge always goes to `agents/sage/` **in the repo** — never to local memory,
never to a scratch file. After writing, record what you learned. Every run must
output exactly one of:

**A — New knowledge.** Create `agents/sage/<domain>/decisions/<slug>.md`.
Write the **pattern**, not the implementation:

- Good: "Team uses CSS custom properties for all color tokens"
- Bad: "ecommerce-landing.md uses `--bg: #0f0f0f`"

Write it so a new team member with no context can apply it next time.
Use this shape: what the pattern is · why · Do / Avoid.
Set `enforcement: advise`, `source: ai`, `status: proposed`.

**B — Updated knowledge.** An existing entry was relevant; note if it was
accurate or stale. Update in place.

**C — No new knowledge.** Existing rules fully covered this.
State it explicitly: `No new knowledge — <file> covers this case.`

One-line entries count. What's not allowed is silence.

---

## Step 5 — Summary (mandatory, every run)

**A response without this block is incomplete.** Output as **plain markdown**
(no code fence) the block that matches your role. Write in **full sentences**
— a field that fits in five words is too abbreviated. Use bullet points for
multi-step content (Mechanism, Fix, Decisions).

**When role = debugger / fixing a bug:**

```markdown
── Sage ──────────────────────────────────────────
**Role** · debugger — <task in one line>
**Model** · <model> @ effort:<effort>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Root cause**
Explain the specific condition, code path, or wrong assumption that caused the
failure. Name the exact function/variable responsible.

**Mechanism**

- <trigger: what initiated the failure>
- <propagation: how it spread to the surface>
- <symptom: what the user or log observed>

**Fix**

- <what changed>
- <why it addresses the root cause>
- <trade-offs or caveats the team should know>

**Validated**
State the concrete evidence you observed — network tab, log output, test result,
manual check. "Looks correct" is not validation.

**Slipped**
Explain why this wasn't caught earlier — missing test, non-obvious API behaviour,
misleading naming, or an assumption that turned out wrong.

**Knowledge** · [new] `<path>` — <pattern title>
──────────────────────────────────────────────────
```

**When role = dev / architect / frontend / any build task:**

```markdown
── Sage ──────────────────────────────────────────
**Role** · <role> — <task in one line>
**Model** · <model> @ effort:<effort>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Done**
Describe what was built or changed — sections, files, and their purpose.

**Decisions**

- <key choice and why>
- <alternatives considered and ruled out>

**Validated**
Describe how you confirmed it works — what you ran, what you checked, what the
output looked like.

**Knowledge** · [new | updated | none] `<path>` — <pattern or reason>
──────────────────────────────────────────────────
```
