# /sage — Universal AI coding command

Use `/sage` before any non-trivial code-changing task. This command is designed for all-around software work across frontend, backend, full-stack, mobile, desktop, CLI, database, data, ML, infrastructure, DevOps, security, generated code, and documentation changes.

`/sage` must work across interactive agents, CLI agents, IDE agents, and headless automation. It must not depend on one provider, one model family, one programming language, one framework, one UI picker, or one proprietary prompt widget.

For code-changing tasks, Steps 1-5 are mandatory. For pure questions, advice, explanations, reviews, translations, or planning with no file changes, answer directly without running `/sage`.

---

## Command modes

`/sage` has two modes:

- `auto` — the agent decides which steps apply, shows the full checklist with recommendations, and proceeds without asking for checklist input.
- `ask` — the agent shows the full checklist every time and waits for the human to choose.

Do not use the old names `smart` or `always` in new config.

Backward compatibility:

- old `askMode: "smart"` means new `mode: "auto"`;
- old `askMode: "always"` means new `mode: "ask"`.

If old config is found, migrate it automatically while preserving unknown fields.

---

## Changing settings

To change `/sage` settings (mode, default steps) use **`/sage-setting`** — it reads and writes `.sage-local.json` for you. Do not ask users to hand-edit JSON, and do not embed a config sub-command here.

Default config:

```json
{
  "version": 2,
  "mode": "auto",
  "checklist": {
    "auto-switch-model": true,
    "plan-flow": true,
    "unit-test": true,
    "e2e-test": false,
    "security-review": false
  }
}
```

Config storage rules:

- Read `.sage-local.json` from the active repo root.
- Create it if it does not exist; migrate old `askMode` to `mode` first.
- Add `.sage-local.json` to `.gitignore` if missing.
- Preserve unknown fields when rewriting config.
- Never store per-machine preferences in committed project files.

---

## Core principles

1. **Classify before acting.** Do not treat a question as a code request.
2. **Show all five choices whenever a checklist is shown.** Do not hide choices just because they are not recommended.
3. **Recommend, do not remove.** Each checklist item must be labeled as recommended or not recommended with a reason.
4. **Use `auto` for no-prompt execution.** In `auto` mode, decide the steps yourself and continue.
5. **Use `ask` for explicit human choice.** In `ask` mode, ask every time for code-changing tasks.
6. **Never exceed the current session ceiling.** Use only the model, reasoning, and effort level available in the current session.
7. **Stay language-agnostic.** Detect the repo's stack from files, commands, manifests, build tools, and tests.
8. **Reuse before writing.** Read project rules and existing source before designing new code.
9. **Validate every change.** Run the most relevant checks for the detected stack. If a check cannot run, report exactly why.
10. **Capture transferable knowledge.** Record patterns, conventions, and decisions, not one-off implementation notes.
11. **Summarize with evidence.** The final summary must include changed files, validation, docs status, remaining risks, and knowledge status.

---

## Step 0 — Classify, recommend, and select steps

### Step 0a — classify the request

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

A request **is a code request** when it changes any of the following: source code, tests, docs, configuration, schemas, APIs, UI, generated assets, build/deploy/CI/infrastructure files, migrations, repository state, or runtime behavior.

---

### Step 0b — read and normalize config

Read `.sage-local.json` at the active repo root. If it contains the old `askMode` field, normalize it: `askMode: "smart"` → `mode: "auto"`; `askMode: "always"` → `mode: "ask"` (set `version: 2`, preserve unknown fields, write it back).

If config is missing, create the default config with `mode: "auto"`. If `.gitignore` does not include `.sage-local.json`, add it.

---

### Step 0c — detect task signals

Do not rely on a fixed "task type" table. Detect signals instead. A task may match many signals.

| Signal              | Examples                                                                  |
| ------------------- | ------------------------------------------------------------------------- |
| `mechanical`        | typo, rename, comment, formatting, import, literal one-line change        |
| `logic`             | conditions, algorithms, parsing, validation, state, business rules        |
| `multi-file`        | coordinated change across modules, packages, layers, or repos             |
| `frontend-ui`       | components, forms, routing, accessibility, visual behavior, state         |
| `backend-api`       | endpoints, controllers, handlers, RPC, GraphQL, queues, jobs              |
| `database`          | schema, migration, query, ORM, index, transaction, seed data              |
| `auth-security`     | auth, roles, permissions, sessions, tokens, secrets, PII, money           |
| `infra-devops`      | Docker, Kubernetes, Terraform, CI/CD, deploy, networking, observability   |
| `mobile-desktop`    | iOS, Android, Flutter, React Native, desktop app, native UI flow          |
| `cli-tooling`       | command behavior, flags, scripts, developer tools, generators             |
| `data-ml`           | ETL, analytics, notebooks, model code, data validation, feature pipelines |
| `performance`       | latency, memory, CPU, concurrency, caching, bundle size, load             |
| `bug-investigation` | logs, failing tests, root cause, regression, flaky behavior               |
| `dependency`        | package upgrade, lockfile, framework version, transitive security risk    |
| `docs-only`         | README, API docs, runbook, changelog, examples                            |
| `generated-code`    | OpenAPI clients, Prisma, protobuf, GraphQL types, SDKs                    |
| `public-contract`   | API shape, CLI output, user flow, config format, DB contract              |

When unsure, choose the safer recommendation.

---

### Step 0d — always keep the same five choices

These are the only checklist choices. Always show all five when a checklist is shown.

1. **auto-switch-model** — pick the best available model or reasoning tier within the current session ceiling
2. **plan-flow** — design and verify the flow before coding (`/sage-flow`)
3. **unit-test** — write or update focused tests for changed logic (`/sage-unit-test`)
4. **e2e-test** — verify behavior end-to-end through UI, API, CLI, integration, browser, mobile, desktop, or load checks (`/sage-e2e-test`)
5. **security-review** — review sensitive, exposed, or abuse-prone changes for holes (`/sage-security-review`)

Do not add a sixth option. Do not add `None`. Do not add `just answer`. Pure questions never reach this step.

---

### Step 0e — recommendation engine

For each of the five choices, produce a status (`recommended` or `not recommended`) and a one-line reason tied to the detected signals.

- **auto-switch-model** — recommend when model/reasoning selection is available and the task is non-trivial or benefits from different tiers across phases. Not recommended when the user pinned a model, there is no model selection, or the edit is fully mechanical. Keep it visible either way.
- **plan-flow** — recommend for `logic`, `multi-file`, `backend-api`, `database`, `auth-security`, `infra-devops`, `mobile-desktop`, `data-ml`, `performance`, `bug-investigation`, `dependency`, `generated-code`, `public-contract`, or meaningful uncertainty. Not for fully specified mechanical or tiny docs-only edits.
- **unit-test** — recommend when the change affects logic, validation, algorithms, parsing, data transforms, API behavior, DB queries, permissions, jobs, CLI output, service boundaries, bug fixes, or regression-prone behavior. Not for purely mechanical, visual-copy, or docs-only changes (unless the repo has doc tests that must compile).
- **e2e-test** — recommend when the change affects an observable flow across boundaries (frontend/mobile/desktop journey, API request/response, CLI behavior, migration applied through the app, auth/session, checkout/payment, upload/download, queue/job, deploy/infra workflow, performance path, generated client/server contract). Not for isolated pure logic with adequate unit coverage and no external flow.
- **security-review** — recommend when the change touches or may expose authn/authz, roles/permissions, sessions/cookies/JWT/OAuth/API keys, secrets/env, PII/money/billing, uploads/downloads/paths/deserialization/UGC, SQL/NoSQL/shell/template/SSRF, dependency upgrades, infra/CI/containers/networking/CORS/CSP, logging of sensitive data, or public APIs/webhooks. Not for isolated mechanical edits, pure styling, or docs-only with no sensitive content.

---

### Step 0f — selection behavior by mode

**Mode `auto`:** detect signals → show the full checklist with `recommended`/`not recommended` labels → enable all recommended choices → do not ask → continue.

```text
Checklist · mode:auto
1. ✓ auto-switch-model — recommended: multi-phase backend change.
2. ✓ plan-flow — recommended: API contract and database behavior may change.
3. ✓ unit-test — recommended: validation logic changes.
4. ~~e2e-test~~ — not recommended: no cross-boundary user flow changed.
5. ✓ security-review — recommended: permissions are affected.
Validation: required. Docs: update only if behavior, API, setup, or public usage changed.
```

**Mode `ask`:** detect signals → show the full checklist with labels → wait for the human → persist the selected checklist as defaults → continue only after they answer.

Preferred structured picker, else Markdown fallback (numbers, e.g. `1,2,3`):

```text
Task: <task in one line>. Which /sage steps should run?

1. auto-switch-model — recommended/not recommended: <reason>
2. plan-flow — recommended/not recommended: <reason>
3. unit-test — recommended/not recommended: <reason>
4. e2e-test — recommended/not recommended: <reason>
5. security-review — recommended/not recommended: <reason>
```

If the environment is headless and cannot ask, behave like `auto` mode and state that prompting is unavailable.

---

## Model and reasoning tier

Read the actual model, reasoning, and effort capability from the current session context when the environment exposes it. Do not recall from memory or assume from a previous run. The session ceiling is the maximum available model and effort in the current session — never exceed it. If the environment does not expose the model/effort, write `Model : current agent @ effort:unavailable`, do not claim model switching, and continue.

Use provider-neutral tiers internally:

| Tier       | Meaning                                                                              |
| ---------- | ------------------------------------------------------------------------------------ |
| `fast`     | Mechanical edits, formatting, trivial file reads, simple rewrites                    |
| `standard` | Normal implementation, focused tests, small refactors, moderate reasoning            |
| `deep`     | Architecture, flow design, root cause, security, migrations, data, schema, high risk |

| Provider capability       | `fast` example           | `standard` example       | `deep` example          |
| ------------------------- | ------------------------ | ------------------------ | ----------------------- |
| Claude-style models       | Haiku/low if available   | Sonnet/current effort    | Opus or session ceiling |
| OpenAI/Codex-style agents | current model/low effort | current model/medium cap | current model/high cap  |
| Fixed-model IDE agent     | current model            | current model            | current model           |
| Unknown provider          | current agent            | current agent            | current agent           |

These are examples, not requirements; the session ceiling always wins. You may go below the session effort for trivial work, never above it. If effort is unavailable, do not invent it. If `plan-flow` is selected, run it at the full session ceiling — never downgrade flow design.

---

## Universal programming coverage

Before coding, detect the repo's stack from real files. Do not assume JavaScript, TypeScript, or web by default.

| Area                  | Common indicators                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------- |
| JavaScript/TypeScript | `package.json`, `pnpm-lock.yaml`, `tsconfig.json`, `vite.config.*`, `next.config.*`           |
| Python                | `pyproject.toml`, `requirements.txt`, `poetry.lock`, `uv.lock`, `setup.py`                    |
| Go                    | `go.mod`, `go.sum`                                                                            |
| Rust                  | `Cargo.toml`, `Cargo.lock`                                                                    |
| Java/Kotlin           | `pom.xml`, `build.gradle`, `settings.gradle`, `gradle.properties`                             |
| .NET                  | `*.csproj`, `*.sln`, `global.json`                                                            |
| PHP                   | `composer.json`, `artisan`, `symfony.lock`                                                    |
| Ruby                  | `Gemfile`, `Rakefile`, `*.gemspec`                                                            |
| Swift/iOS             | `Package.swift`, `*.xcodeproj`, `*.xcworkspace`, `Podfile`                                    |
| Android               | `build.gradle`, `AndroidManifest.xml`, `settings.gradle`                                      |
| Dart/Flutter          | `pubspec.yaml`                                                                                |
| C/C++                 | `CMakeLists.txt`, `Makefile`, `meson.build`, `conanfile.*`                                    |
| SQL/DB                | `migrations/`, `schema.prisma`, `dbt_project.yml`, `*.sql`                                    |
| Infrastructure        | `Dockerfile`, `compose.yaml`, `k8s/`, `helm/`, `*.tf`, `.github/workflows/`, `.gitlab-ci.yml` |
| Data/ML               | `notebooks/`, `dvc.yaml`, `mlflow`, `airflow/`, `dbt_project.yml`                             |
| Docs                  | `README*`, `docs/`, `mkdocs.yml`, `docusaurus.config.*`                                       |

Use the detected stack to choose roles, assets, validation, and test strategy.

---

## Universal role lenses

Pick the expert lens the task needs; do not default to `dev`. Roles may hand off between phases.

`architect` · `fullstack` · `frontend` · `backend` · `mobile` · `desktop` · `cli` · `database` · `data` · `ml` · `infra` · `devops` · `security` · `qa` · `debugger` · `performance` · `writer` — or any lens the task implies.

Before each phase, load `agents/sage/roles/role-<lens>.md`. If it exists, read and adopt it. If missing, create a small role file in the Sage **Ikigai** format:

```markdown
---
role: <lens>
title: Senior <Lens>
covers: [<domains>]
updated: <today>
---

## Ikigai

- Loves — <what this role optimizes for>
- Good at — <specific expertise, stack, patterns, and failure modes>
- Team needs — <how this role protects the project>
- Worth it — <why this role matters>

## How I work

- Reuse existing rules and assets before writing new code.
- Name the blast radius before changing behavior.
- Validate with the closest reliable check for this stack.
- Stop on unclear high-risk changes.
```

Output `Role: <lens> [loaded]` or `Role: <lens> [created]`, and on handoff `Role: <next> [loaded] — handoff from <prev>`.

---

## Step 1 — Load roles

Select the role(s) from the detected signals and stack, load or create the role files, output the role lines before the phase that uses them, and hand off roles explicitly when the phase changes.

---

## Step 2 — Read knowledge and reusable assets

**Step 2a — project knowledge.** Open `agents/sage/<domain>/rules.md` and relevant `agents/sage/<domain>/decisions/*.md`. Quote only the rules that apply, and respect each rule's `enforcement` (`block` = must/never · `warn` = strong preference · `advise` = guidance — see `AGENTS.md` §5). If the domain folder or rules file is missing, say so and continue; create knowledge only in Step 4.

**Step 2b — reusable assets.** Search for existing utilities, hooks, components, services, commands, validators, schemas, fixtures, generated clients, migrations, test helpers, CI jobs, deploy scripts, and runbooks before writing new ones. When you find one, **open the source file and read its exports / public API / command behavior** — never infer from a name, README, or decision file. Report only the assets that matter.

---

## Step 3 — State intent and plan before writing

Output the intent block before making changes. For LOW-risk small changes, show intent and proceed. For MEDIUM/HIGH risk, multi-file features, schema/API changes, auth/money/PII, infrastructure, migrations, or meaningful uncertainty, show intent and wait for approval unless the user requested autonomous execution.

```text
Repo    : <repo-root>
Role    : <role> — <one-line task summary>
Model   : <model or current agent> @ effort:<effort or unavailable>
Intent  : <what this change will do>
Touches : <files, systems, domains affected>
Risk    : LOW | MEDIUM | HIGH — <why in one phrase>
Decision: proceed | warn | ask | reject
```

`proceed` = safe to continue · `warn` = continue but name a caveat · `ask` = need approval/info before changing files · `reject` = unsafe or impossible.

**Step 3a — plan.** Identify parallel vs sequential work; annotate each task with owner role, tier (`fast`/`standard`/`deep`), effort if available, dependency, and expected validation.

```text
Plan (session ceiling: <model or current agent> @ effort:<effort or unavailable>)
── Phase 1 [parallel] ─────────────────────────
  A. Read existing API contract              role: backend   tier: standard   effort: <= ceiling
  B. Read database migration conventions     role: database  tier: standard   effort: <= ceiling
── Phase 2 [sequential] ───────────────────────
  C. Implement compatible schema change      role: backend   tier: deep       depends on A+B
── Phase 3 [parallel] ─────────────────────────
  D. Add regression tests                    role: qa        tier: standard   depends on C
  E. Run migration dry-run and type checks   role: qa        tier: standard   depends on C
```

**Step 3b — progress.** Mark task starts/completions as they happen; report results without waiting for the whole phase. On a failure that affects correctness, report immediately and pause. For non-blocking failures, continue only if the remaining path is safe and say why.

---

## Write the code

Keep changes scoped to the intent; reuse existing assets first; follow project naming/folder conventions; avoid unrelated cleanup and broad rewrites unless the plan approved them; preserve public contracts unless intentionally changing them; keep frontend/backend contracts aligned; protect data integrity and migration safety; keep the generated-code source of truth clear; add tests when `unit-test`/`e2e-test` applies; update docs only when behavior, setup, API, public usage, configuration, deployment, or team decisions changed.

---

## Universal validation rules

Validation is mandatory, but exact commands depend on the detected stack. Prefer commands already defined in the repo. Run the closest relevant checks:

| Stack or area         | Common validation commands                                                          |
| --------------------- | ----------------------------------------------------------------------------------- |
| JavaScript/TypeScript | `npm test`, `pnpm test`, `npm run typecheck`, `pnpm lint`, `npm run build`          |
| Python                | `pytest`, `ruff check`, `mypy`, `pyright`, `uv run pytest`                          |
| Go                    | `go test ./...`, `go vet ./...`, `golangci-lint run`                                |
| Rust                  | `cargo test`, `cargo clippy`, `cargo fmt --check`, `cargo build`                    |
| Java/Kotlin           | `mvn test`, `mvn verify`, `gradle test`, `gradle build`                             |
| .NET                  | `dotnet test`, `dotnet build`, `dotnet format --verify-no-changes`                  |
| PHP                   | `composer test`, `phpunit`, `pest`, `phpstan`, `psalm`                              |
| Ruby                  | `bundle exec rspec`, `rails test`, `bundle exec rubocop`                            |
| Swift/iOS             | `swift test`, `xcodebuild test`                                                     |
| Android               | `./gradlew test`, `./gradlew connectedAndroidTest`, `./gradlew lint`                |
| Flutter/Dart          | `flutter test`, `dart test`, `dart analyze`, `flutter build`                        |
| C/C++                 | `ctest`, `cmake --build`, `make test`, `ninja test`                                 |
| Database              | migration dry-run, rollback check, query plan check, seed validation                |
| Infra/DevOps          | `terraform validate`, `terraform plan`, `helm lint`, `kubectl diff`, `docker build` |
| Frontend E2E          | Playwright, Cypress, Storybook test, accessibility scan when available              |
| API E2E               | contract tests, integration tests, Postman/Newman, smoke request                    |
| CLI E2E               | command invocation with expected exit code and output                               |
| Performance           | benchmark, profiler, load test, bundle analyzer, query plan                         |
| Docs                  | doc build, markdown lint, examples compile, generated docs diff                     |

If a check is unavailable or cannot run, state the exact reason. Documentation is required only when the change affects external behavior, setup, deployment, API contracts, public flows, configuration, team decisions, or reusable patterns; otherwise say why docs were skipped.

---

## Step 4 — Capture knowledge

Knowledge always goes to `agents/sage/` inside the active repo. Never store project knowledge in local memory, a scratch file, or another repo.

First analyze the whole run, then split by topic. Review the conversation, files created/changed, validation results, and corrections. Capture **every distinct transferable pattern** — a real run may produce more than one (architecture boundary, naming convention, validation rule, library gotcha, testing pattern, security rule, migration pattern, frontend/backend contract rule, deployment rule, performance constraint). **Do not reduce multiple patterns into one vague summary.** Every run outputs one of:

- **A — New knowledge (one file per idea):** `agents/sage/<domain>/decisions/<slug>.md` (frontmatter format in `AGENTS.md` §2). Write the **pattern**, not the implementation. Good: "Forms must use the shared resolver so client and server validation stay aligned." Bad: "Fixed CreateUserForm.tsx by adding valibotResolver." Two unrelated patterns = two files, in the correct domains. `status: proposed`, `source: ai`, sensible `enforcement`.
- **B — Updated knowledge:** update the existing file in place when it was relevant but incomplete, stale, or corrected by this run.
- **C — No new knowledge:** only when nothing transfers. State it: `Knowledge · [none] agents/sage/<domain>/rules.md — Existing rules fully covered this case.` Silence is not allowed.

---

## Step 5 — Summary

A response without this block is incomplete for code-changing tasks. Output as plain Markdown (no code fence). Use complete sentences; include concrete files, commands, and evidence.

**Debugger / bug fix:**

```markdown
── Sage ──────────────────────────────────────────
**Role** · debugger — <task in one line>
**Model** · <model or current agent> @ effort:<effort or unavailable>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Root cause**
The specific condition, code path, wrong assumption, config, query, or dependency that caused the failure.

**Mechanism**

- <trigger> · <propagation> · <symptom>

**Changed**

- `<file>` — <what changed and why>

**Fix**

- <why it addresses the root cause> · <trade-offs>

**Validated**

- `<command or check>` — <passed | failed | skipped with exact reason>

**Docs**

- <updated path, or skipped with exact reason>

**Slipped**
Why it was not caught earlier.

**Remaining**

- <known limitation, follow-up, or "None">

**Knowledge** · [new | updated | none] `<path>` — <pattern title or reason>
──────────────────────────────────────────────────
```

**Build / implementation (dev, architect, frontend, backend, fullstack, mobile, desktop, cli, database, data, ml, infra, devops, security, qa, performance, writer):**

```markdown
── Sage ──────────────────────────────────────────
**Role** · <role> — <task in one line>
**Model** · <model or current agent> @ effort:<effort or unavailable>
**Domain** · <domain> | **Risk** · <LOW | MEDIUM | HIGH>

**Changed**

- `<file>` — <what changed and why>

**Decisions**

- <key choice and why> · <alternative ruled out>

**Validated**

- `<command or check>` — <passed | failed | skipped with exact reason>

**Docs**

- <updated path, or skipped with exact reason>

**Remaining**

- <known limitation, follow-up, or "None">

**Knowledge** · [new | updated | none] `<path>` — <pattern title or reason>
──────────────────────────────────────────────────
```

---

## Stop conditions

Stop and ask before changing files when: risk is HIGH and the user has not approved autonomous execution; the request could delete or overwrite user data; the change affects auth/money/PII/security boundaries/production infra and the intent is ambiguous; required source files, contracts, schemas, or migration history are missing; validation cannot be performed and the change is risky; or the user asks for something unsafe. Do not stop for trivial missing preferences when a safe best effort is possible — state the assumption and continue.

---

## Common anti-patterns

Avoid: showing the checklist for a pure question; hiding choices instead of labeling them; depending only on a proprietary picker some tools cannot render; using old mode names `smart`/`always` in new config; saying "AskUserQuestion" when the environment lacks it; assuming JavaScript/TypeScript/web without reading repo indicators; claiming provider-specific models in an unknown-provider environment; raising effort above the session ceiling or downgrading `plan-flow` below it; treating validation as optional or ending with "looks good"; broad unrelated cleanup; updating docs for every tiny edit; writing one vague knowledge file for multiple decisions.

---

## Minimal completion checklist

Before the final response, confirm internally: the request was classified correctly; pure questions skipped the checklist; code requests read/created `.sage-local.json` (old `askMode` migrated to `mode`); mode was `auto` or `ask`; all five choices stayed visible with a recommendation label + reason; role files were loaded/created; rules and assets were checked; the repo stack was detected from real files; intent, risk, and plan were stated with provider-neutral tiers within the ceiling; changes stayed in scope; validation ran or was skipped with an exact reason; docs updated or skipped with a reason; Step 4 knowledge was new/updated/none, split by topic; Step 5 summary included Changed, Decisions or Fix, Validated, Docs, Remaining, and Knowledge.
