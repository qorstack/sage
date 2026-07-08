# /sage — Sage cognition pipeline

Use `/sage` before any non-trivial code-changing task. The pipeline is designed to work across interactive agents, CLI agents, IDE agents, and headless automation. It must not depend on a single provider, model family, UI picker, or proprietary prompt widget.

For code-changing tasks, Steps 1-5 are mandatory. For pure questions, advice, explanations, reviews, translations, or planning with no file changes, answer directly without running `/sage`.

---

## Core principles

1. **Do not treat questions as code requests.** If no files will change, do not show a checklist and do not invent an escape option such as "None" or "just answer".
2. **Ask only when asking helps.** Use the checklist when it is due, but use a Markdown fallback if the environment has no structured picker.
3. **Never exceed the current session ceiling.** Use the model, reasoning, and effort level available in the current session. Do not assume a provider-specific model name.
4. **Prefer reusable knowledge and existing assets.** Read project rules and existing source before designing new code.
5. **Validate every change.** Run the most relevant available checks. If a check cannot run, report exactly why.
6. **Capture transferable knowledge.** Record patterns, conventions, and decisions, not one-off implementation notes.
7. **Summarize with evidence.** The final summary must include changed files, validation, remaining risks, and knowledge status.

---

## Step 0 — Decide whether to ask, then run the checklist

### Step 0 guard — classify the request first

Before doing anything else, classify the request.

A request is **not a code request** when it only asks for:

- an explanation;
- advice;
- a review with no file edits;
- a comparison;
- a translation or rewrite;
- a decision recommendation;
- a pure question such as "should we use pnpm?" or "what does this function do?".

If it is not a code request, answer directly. Do not show the checklist in any mode.

A request **is a code request** when it changes files, behavior, tests, docs, configuration, schemas, APIs, UI, infrastructure, generated assets, or repository state.

---

### Step 0a — read the per-machine preference

Read `.sage-local.json` at the active repo root. The file is local-only and must be gitignored. It stores:

- `askMode`: either `"always"` or `"smart"`;
- `checklist`: the last selected step defaults;
- optional provider or tool preferences if the team adds them later.

If `.sage-local.json` does not exist, this is the first run. Show the checklist and ask how often `/sage` should ask from now on.

Use this shape:

```json
{
  "askMode": "smart",
  "checklist": {
    "auto-switch-model": true,
    "plan-flow": true,
    "unit-test": true,
    "e2e-test": false,
    "security-review": false
  }
}
```

Preserve any unknown fields when rewriting the file. If `.gitignore` does not include `.sage-local.json`, add it.

---

### Step 0b — decide whether the checklist is due

Use the following rules:

- `askMode: "always"` means show the checklist for every code request.
- `askMode: "smart"` means skip only truly trivial changes.
- Treat the task as substantial when it touches logic, control flow, API shape, schema, auth, money, PII, permissions, multiple files, infrastructure, migrations, release behavior, test strategy, or a bug that needs investigation.
- Treat the task as trivial only when it is a fully specified typo, rename, comment, log line, import, formatting change, or literal one-line edit with no behavior decision.
- When unsure, treat the task as substantial.
- If the task needs a plan, always show the checklist and recommend `plan-flow`, even in smart mode.

If the checklist is skipped, state the reason in one line:

```text
Checklist · skipped (trivial: <reason>)
```

Role selection, risk review, validation, and summary still apply to code-changing tasks even when the checklist is skipped.

---

### Step 0c — present the checklist with provider-safe fallback

Use the same five options in the same order every time.

1. **auto-switch-model** — pick the best available model or reasoning tier within the current session ceiling
2. **plan-flow** — design and verify the flow before coding (`/sage-flow`)
3. **unit-test** — write unit tests for changed logic (`/sage-unit-test`)
4. **e2e-test** — drive the flow end-to-end through browser, API, or load checks (`/sage-e2e-test`)
5. **security-review** — review sensitive changes for holes (`/sage-security-review`)

Do not add a sixth option. Do not add `None`. Do not add `just answer`. Pure questions never reach this step.

#### Preferred interactive mode

If the environment supports a structured picker, use it. The picker must contain the exact five options above. It may also ask:

```text
From now on, when should /sage ask this?
- Every time
- Only big changes
```

Map the answer to:

- `Every time` → `askMode: "always"`
- `Only big changes` → `askMode: "smart"`

#### Markdown fallback mode

If the environment does not support a structured picker but can receive text replies, show this exact Markdown fallback:

```text
Task: <task in one line>. Which /sage steps should run?

Reply with numbers, for example: 1,2,3

1. auto-switch-model — auto-pick model + effort per task, within the ceiling
2. plan-flow — design + verify the flow before coding (/sage-flow)
3. unit-test — write unit tests for the changed logic (/sage-unit-test)
4. e2e-test — drive the flow end-to-end, browser/API/load (/sage-e2e-test)
5. security-review — review sensitive changes for holes (/sage-security-review)

Ask mode:
A. Every time
B. Only big changes
```

After the user answers, persist their selections to `.sage-local.json`.

#### Headless mode

If the environment cannot prompt, state that it is non-interactive and apply recommended defaults based on task fit. Never silently run nothing.

Example:

```text
Checklist · non-interactive environment; enabled recommended defaults: auto-switch-model, plan-flow, unit-test. Skipped e2e-test because no runnable UI flow was available. Skipped security-review because the change is not sensitive.
```

Recommended defaults by task type:

| Task type                           | Recommended steps                                        |
| ----------------------------------- | -------------------------------------------------------- |
| Trivial one-line mechanical edit    | auto-switch-model                                        |
| Normal logic change                 | auto-switch-model, unit-test                             |
| Multi-file feature                  | auto-switch-model, plan-flow, unit-test                  |
| UI flow change                      | auto-switch-model, plan-flow, unit-test, e2e-test        |
| Auth, money, PII, permissions       | auto-switch-model, plan-flow, unit-test, security-review |
| Infrastructure or deployment change | auto-switch-model, plan-flow, security-review            |
| Bug requiring investigation         | auto-switch-model, plan-flow, unit-test                  |
| Security bug                        | auto-switch-model, plan-flow, unit-test, security-review |

---

### Step 0d — pre-check honestly

Default checked state starts from `.sage-local.json`, then must be adjusted to fit the current task.

Only check an option when it genuinely applies. Leave the rest unchecked with a short reason. Never check an option whose reason is "not applicable", "maybe", or "only if needed".

`auto-switch-model` defaults on unless the human has pinned a model or the environment does not support model selection.

---

### Step 0e — echo the confirmed checklist

After the user answers, echo the effective checklist in one line before continuing:

```text
Checklist · ✓ auto-switch-model · ✓ plan-flow → /sage-flow · ✓ unit-test · ~~e2e-test~~ (no UI flow) · ~~security-review~~ (not sensitive) · validation: required · docs: update only if behavior/API/setup changed
```

Validation is not a picker item. Documentation is not a picker item. They are handled by the validation and documentation rules below.

Also persist the confirmed `checklist` and `askMode` back to `.sage-local.json`.

---

## Model and reasoning tier — applies to every step

### Detect the session ceiling before each task

Read the actual model, reasoning, and effort capability from the current session context when the environment exposes it. Do not recall from memory and do not assume from a previous run.

The session ceiling is the maximum available model and effort level in the current session. Never exceed it.

If the environment does not expose the model or effort level, write:

```text
Model   : current agent @ effort:unavailable
```

Then do not claim model switching. Use the current agent and continue.

---

### Provider-neutral reasoning tiers

Use provider-neutral tiers internally:

| Tier       | Meaning                                                                  |
| ---------- | ------------------------------------------------------------------------ |
| `fast`     | Mechanical edits, formatting, trivial file reads, simple rewrites        |
| `standard` | Normal implementation, moderate reasoning, tests, small refactors        |
| `deep`     | Architecture, flow design, root cause, security, data, schema, high risk |

A provider may map these tiers to model families, effort settings, or no-op behavior.

Examples:

| Provider capability       | `fast` example           | `standard` example       | `deep` example          |
| ------------------------- | ------------------------ | ------------------------ | ----------------------- |
| Claude-style models       | Haiku/low if available   | Sonnet/current effort    | Opus or session ceiling |
| OpenAI/Codex-style agents | current model/low effort | current model/medium cap | current model/high cap  |
| Fixed-model IDE agent     | current model            | current model            | current model           |
| Unknown provider          | current agent            | current agent            | current agent           |

These are examples, not requirements. The current session ceiling always wins.

---

### Effort levels are caps, not targets

If the session exposes effort levels such as `low`, `medium`, `high`, or `max`, treat the session effort as both the default and the hard ceiling.

- You may go below the session effort for trivial work.
- You may never go above the session effort.
- A difficult task does not justify exceeding the session ceiling.
- If effort is unavailable, do not invent it.

Meaning guide:

| Effort   | Meaning                                                          |
| -------- | ---------------------------------------------------------------- |
| `low`    | Simple edits, file reads, boilerplate, minimal reasoning         |
| `medium` | Standard implementation and moderate complexity                  |
| `high`   | Complex logic, root cause, architecture, risky decisions         |
| `max`    | Hardest multi-system problems, only when available and permitted |

---

### How to pick a task tier

1. Identify the session ceiling.
2. Use `deep` for `plan-flow`, architecture, security, migrations, money/auth/PII, root cause, and high-risk decisions.
3. Use `standard` for normal implementation, refactors, unit tests, and moderate logic.
4. Use `fast` only for mechanical, fully specified edits with no judgment.
5. Never exceed the session ceiling.
6. If `plan-flow` is selected, run it at the full session ceiling. Do not downgrade flow design.

State the detected model once in Step 3. Annotate each plan task with the selected provider-neutral tier and effort when available.

---

## Multi-repo workspace rule

When multiple repositories are open, anchor every path to the repo root that owns the file being edited. Find it by locating the closest ancestor directory that contains `AGENTS.md`, `.git`, or the project-level config used by the workspace.

State the active repo once in Step 3:

```text
Repo    : <repo-root>
```

Do not read knowledge from another repo. Do not write knowledge outside the active repo's `agents/sage/` directory.

---

## Step 1 — Load role lenses

Pick the expert lens the task needs. Do not default to `dev` when another lens is more accurate.

Common lenses:

- `architect` — approach, boundaries, system design, sequencing
- `dev` — implementation
- `frontend` — UI, UX behavior, accessibility, state, forms
- `backend` — APIs, persistence, jobs, integrations
- `infra` — deployment, CI, containers, networking, observability
- `security` — auth, permissions, secrets, PII, money, abuse cases
- `qa` — tests, acceptance criteria, reproducibility, regression risk
- `debugger` — root cause, logs, failure mechanism, fix verification
- `data` — schemas, migrations, analytics, data integrity
- `writer` — docs, naming, copy, changelogs

Roles may hand off between phases. For example:

```text
Role: architect [loaded]
Role: dev [loaded] — handoff from architect
Role: qa [loaded] — handoff from dev
```

Before each phase, load the relevant role file at `agents/sage/roles/role-<lens>.md`. If it exists, read it and adopt it.

If the file is missing, create it in the Sage role format (see `AGENTS.md` §2) — the **Ikigai** persona (Loves · Good at · Team needs · Worth it) plus a **How I work** section. Keep it small; the "Good at" list is the point.

Output one line after loading or creating a role:

```text
Role: <lens> [loaded]
```

or:

```text
Role: <lens> [created]
```

---

## Step 2 — Read knowledge and find reusable assets

### Step 2a — read project knowledge

Open the relevant domain rules at `agents/sage/<domain>/rules.md` and any relevant decision files at `agents/sage/<domain>/decisions/*.md`.

Quote the specific rules that apply. Do not quote unrelated rules. Respect each rule's `enforcement` (`block` = must/never · `warn` = prefer · `advise` = consider — see `AGENTS.md` §5).

If the domain folder or rules file is missing, say so and continue. Do not create `rules.md` merely because it is missing. Create or update knowledge only in Step 4 when the run produces transferable knowledge.

Example:

```text
Knowledge checked:
- agents/sage/frontend/rules.md — "Forms use the shared resolver and never bypass validation."
- agents/sage/security/decisions/token-role-source.md — "Permissions are resolved server-side; UI state is not authoritative."
```

### Step 2b — find reusable assets

Search for existing utilities, hooks, components, services, commands, validators, schemas, fixtures, or test helpers before writing new ones.

When you find a reusable asset, open the source file and read its exports. Never infer an API from a name, README, or decision file. Source is authoritative.

Report only the assets that matter:

```text
Assets checked:
- src/features/orders/useOrderFilters.ts — exports `useOrderFilters` and `serializeOrderFilters`.
- src/lib/auth/requirePermission.ts — exports `requirePermission` for server-side checks.
```

---

## Step 3 — State intent and plan before writing

Output the intent block before making changes.

For LOW-risk small changes, show the intent and proceed without waiting. For MEDIUM or HIGH risk, multi-file features, schema/API changes, auth/money/PII, infrastructure, migrations, or meaningful uncertainty, show the intent and wait for approval.

Use `Decision` as follows:

- `proceed` — safe to continue without approval;
- `warn` — continue, but clearly name a caveat;
- `ask` — approval or missing information is needed before changing files;
- `reject` — do not proceed because the request is unsafe or impossible.

```text
Repo    : <repo-root>  # include only when useful or in multi-repo workspaces
Role    : <role> — <one-line task summary>
Model   : <model or current agent> @ effort:<effort or unavailable>
Intent  : <what this change will do>
Touches : <files, systems, domains affected>
Risk    : LOW | MEDIUM | HIGH — <why in one phrase>
Decision: proceed | warn | ask | reject
```

### Step 3a — declare the plan

Before listing tasks, identify what can run in parallel and what must be sequential. Annotate every task with its owner role, reasoning tier (`fast`, `standard`, `deep`), effort if available, and dependency if any.

```text
Plan (session ceiling: <model or current agent> @ effort:<effort or unavailable>)
── Phase 1 [parallel] ─────────────────────────
  A. Read form schema and existing resolver        role: frontend   tier: standard   effort: <= ceiling
  B. Read API contract and validation rules        role: backend    tier: standard   effort: <= ceiling
── Phase 2 [sequential] ───────────────────────
  C. Implement shared validation path              role: dev        tier: standard   depends on A+B
── Phase 3 [parallel] ─────────────────────────
  D. Add unit tests for invalid submissions        role: qa         tier: standard   depends on C
  E. Run validation and summarize                  role: qa         tier: fast       depends on C+D
```

### Step 3b — progress reporting

When executing, mark task starts and completions. Do not wait until the entire phase ends to report useful results.

```text
── [phase 1 · parallel: A, B] ────────────────
  🟨 A [frontend/standard] — Reading existing form schema.
  ✅ A — Found shared resolver and current bypass point.
  🟨 B [backend/standard] — Reading API contract.
  ✅ B — API rejects unknown enum values server-side.
── [phase 1 → all done, proceeding to phase 2] ──
```

If a task fails, report it immediately and pause when the failure affects correctness:

```text
❌ B — Could not find the API contract. Pausing because changing validation without the contract may break submissions.
```

For non-blocking failures, continue only if the remaining path is still safe and say why.

---

## Write the code

When writing code:

- keep changes scoped to the stated intent;
- reuse existing assets first;
- follow project naming and folder conventions;
- avoid unrelated cleanup;
- avoid broad rewrites unless the plan approved them;
- add tests when `unit-test` or `e2e-test` applies;
- update docs only when behavior, setup, API, public usage, or team decisions changed.

---

## Validation and documentation rules

Validation is mandatory, but the exact command depends on the repo. Run the most relevant available checks: unit tests for changed logic; e2e tests for changed user flows; typecheck for typed codebases; lint for style/static errors; build for integration errors; migration dry-run or schema validation for database changes; a manual browser/API check when automation is unavailable.

If a check is unavailable or cannot run, state the exact reason.

```text
Validation:
- `pnpm test -- user-form` — passed.
- `pnpm typecheck` — passed.
- `pnpm e2e` — skipped because no browser environment is available in this agent.
```

Documentation is required only when the change affects external behavior, setup or deployment, API contracts, public user flows, configuration, team decisions, or reusable patterns. If docs do not need updates, say why:

```text
Docs: skipped because the change is internal refactoring with no behavior, setup, or API change.
```

---

## Step 4 — Capture knowledge

Knowledge always goes to `agents/sage/` inside the active repo. Never store project knowledge in local memory, a scratch file, or another repo.

First analyze the whole run, then split by topic. Review the conversation, files created or changed, validation results, and corrections from the user. Capture **every distinct transferable pattern** — a real run may produce more than one:

- an architecture boundary;
- a naming convention;
- a validation rule;
- a library gotcha;
- a testing pattern;
- a security rule.

**Do not reduce multiple patterns into one vague summary.** Every run must output one of:

**A — New knowledge (one file per idea).** Create `agents/sage/<domain>/decisions/<slug>.md` (frontmatter format in `AGENTS.md` §2). Write the **pattern**, not the implementation:

- Good: "Forms must use the shared resolver so client and server validation stay aligned."
- Bad: "Fixed `CreateUserForm.tsx` by adding `valibotResolver`."

Two unrelated patterns must become two files, in the correct domains. Set `status: proposed`, `source: ai`, and a sensible `enforcement`.

**B — Updated knowledge.** Update the existing file in place when it was relevant but incomplete, stale, or corrected by this run.

**C — No new knowledge.** Only when nothing transfers beyond the current implementation. State it: `Knowledge · [none] agents/sage/<domain>/rules.md — Existing rules fully covered this case.` Silence is not allowed.

---

## Step 5 — Summary

A response without this block is incomplete for code-changing tasks. Output the block as plain Markdown, not inside a code fence. Use complete sentences; include concrete files, commands, and evidence.

### Summary for debugger or bug-fix work

```markdown
── Sage ──────────────────────────────────────────
**Role** · debugger — <task in one line>
**Model** · <model or current agent> @ effort:<effort or unavailable>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Root cause**
Explain the specific condition, code path, or wrong assumption that caused the failure. Name the exact function, variable, config, query, or dependency responsible.

**Mechanism**

- <trigger: what initiated the failure>
- <propagation: how it moved through the system>
- <symptom: what the user, log, test, or monitor observed>

**Changed**

- `<file>` — <what changed and why>

**Fix**

- <why the change addresses the root cause>
- <trade-offs or caveats the team should know>

**Validated**

- `<command or check>` — <passed, failed, or skipped with exact reason>

**Slipped**
Explain why this was not caught earlier — missing test, non-obvious API behavior, misleading naming, weak monitoring, or a wrong assumption.

**Remaining**

- <known limitation, follow-up, or "None">

**Knowledge** · [new | updated | none] `<path>` — <pattern title or reason>
──────────────────────────────────────────────────
```

### Summary for dev, architect, frontend, backend, infra, data, writer, or build work

```markdown
── Sage ──────────────────────────────────────────
**Role** · <role> — <task in one line>
**Model** · <model or current agent> @ effort:<effort or unavailable>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Changed**

- `<file>` — <what changed and why>

**Decisions**

- <key choice and why>
- <alternative considered and why it was not used>

**Validated**

- `<command or check>` — <passed, failed, or skipped with exact reason>

**Docs**

- <updated path, or skipped with exact reason>

**Remaining**

- <known limitation, follow-up, or "None">

**Knowledge** · [new | updated | none] `<path>` — <pattern title or reason>
──────────────────────────────────────────────────
```

---

## Stop conditions

Stop and ask before changing files when:

- risk is HIGH and the user has not explicitly approved;
- the request could delete or overwrite user data;
- the change affects auth, money, PII, security boundaries, or production infrastructure and the intent is ambiguous;
- required source files or contracts are missing;
- validation cannot be performed and the change is risky;
- the user asks for something unsafe or outside allowed capabilities.

Do not stop for trivial missing preferences when a safe best effort is possible. Make the best safe assumption, state it, and continue.

---

## Common anti-patterns

Avoid these:

- Showing the checklist for a pure question.
- Depending only on a proprietary picker that some tools cannot render — always have the Markdown fallback.
- Saying "AskUserQuestion" when the environment does not have that tool.
- Claiming Claude-specific models in a Codex or unknown-provider environment.
- Raising effort above the session ceiling; downgrading `plan-flow` below it.
- Treating validation as optional, or ending with "looks good" instead of concrete evidence.
- Running broad unrelated cleanup, or updating docs for every tiny internal edit.
- Writing one vague knowledge file for multiple unrelated decisions.

---

## Minimal completion checklist

Before the final response, confirm internally:

- the request was classified correctly; pure questions skipped the checklist;
- code requests used the picker, Markdown fallback, or headless defaults;
- `.sage-local.json` was read or created and is gitignored;
- role files were loaded or created; relevant rules and assets were checked;
- intent, risk, and plan were stated; the plan used provider-neutral tiers within the ceiling;
- changes stayed in scope; validation ran or was skipped with an exact reason;
- docs were updated or skipped with an exact reason;
- Step 4 knowledge was new, updated, or explicitly none (split by topic);
- Step 5 summary included Changed, Decisions or Fix, Validated, Docs, Remaining, and Knowledge.
