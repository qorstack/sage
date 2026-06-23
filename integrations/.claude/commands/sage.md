# /sage — Sage cognition pipeline

Run before any non-trivial code change. Steps 1–3 run **before** you write code.
Steps 4–5 run **after**. All five are mandatory — never skip, never abbreviate.

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

**Ceiling: the model and effort active in this session.** Never exceed either.
Pick the lowest tier that adequately covers each task — downgrade aggressively
for mechanical work to save tokens:

| Model    | Effort   | When to use                                                        |
| -------- | -------- | ------------------------------------------------------------------ |
| `haiku`  | `low`    | File reads, simple edits, boilerplate — no reasoning needed        |
| `sonnet` | `medium` | Standard implementation, moderate complexity                       |
| `opus`   | `high`   | Complex logic, architecture, root-cause, critical decisions        |
| `opus`   | `max`    | Hardest multi-system problems — reserve for when high isn't enough |

State model + effort for every task in the plan:

```text
Plan
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
