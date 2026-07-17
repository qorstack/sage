# /sage — Universal AI coding command

Use `/sage` before any non-trivial code-changing task. This command is designed for all-around software work across frontend, backend, full-stack, mobile, desktop, CLI, database, data, ML, infrastructure, DevOps, security, generated code, and documentation changes.

`/sage` must work across interactive agents, CLI agents, IDE agents, and headless automation. It must not depend on one provider, one model family, one programming language, one framework, one UI picker, or one proprietary prompt widget.

For code-changing tasks, Steps 1-5 are mandatory. For pure questions, advice, explanations, reviews, translations, or planning with no file changes, answer directly without running `/sage`.

> **Source of truth — read this before editing.** `AGENTS.md` owns the protocol:
> role selection (§1–§2), the risk header (§4), knowledge capture (§3),
> enforcement (§5), and the summary block (§4b). This command file owns only what
> `AGENTS.md` does **not**: the checklist mechanics (config, signals,
> recommendation engine) and the stack/validation tables. Where the two overlap,
> **`AGENTS.md` wins — point to it, don't restate it here** (restating is what
> makes the two drift).

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

The operating principles are `AGENTS.md`'s pipeline (§0–§5) applied to this command: classify before acting · show all five choices with honest recommendations · never exceed the session ceiling · stay language-agnostic (detect the stack from real files) · reuse before writing · validate every change or say why you can't · capture only transferable knowledge · summarize with evidence. The steps below are the operational detail; `AGENTS.md` is authoritative wherever they overlap.

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

### Step 0c — route the request and detect task signals

Assign the preliminary route defined in `AGENTS.md` §0:

| Route | Trigger | Required next step |
| --- | --- | --- |
| `clear-single-session` | intent, terms, scope, trade-offs settled | checklist → flow/build |
| `foggy-single-session` | genuine decisions remain but fit one session | `/sage-grill` before design |
| `large-multi-session` | destination still foggy beyond one session | `/sage-wayfinder` before flow |

Routing is always-on and independent of `plan-flow`. Do not use file count or
risk level as a proxy for fog. Confirm the route after reading knowledge and
source in Step 2; facts may shrink the fog or expose a larger effort.

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

1. **auto-switch-model** — right-size reasoning: pick the effort/reasoning tier within the ceiling, and push a down-shiftable sub-task to a smaller, cheaper sub-agent to save tokens (only when the task is big enough to beat the sub-agent's overhead). Never above the session model/effort — a hard cost ceiling so nothing burns tokens unbudgeted; does not change the running session model
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

Checklist recommendations and risk controls are related but not interchangeable.
The checklist selects applicable specialist workflows; the driver table in
`AGENTS.md` §1.4 assigns core controls that remain required even when no
specialist applies or the human disables one. Never turn every HIGH risk into a
security review, and never treat an unchecked specialist as removal of a core
control.

---

### Step 0f — selection behavior by mode

**Mode `auto`:** detect signals → show the full checklist with `recommended`/`not recommended` labels → enable all recommended choices → do not ask about the checklist → continue. This mode never bypasses a HIGH-risk gate, genuine HITL decision, destructive approval, or matched `block` rule.

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

Follow the model/effort discipline in **`AGENTS.md` §1.4**: read the real session model/effort (never recall from memory); it is the hard ceiling on both **capability and cost**; you cannot raise the running session's model, so "switching" means picking the effort tier and pushing a down-shiftable sub-task to a smaller, cheaper sub-agent — only downward, never above the ceiling, never a switch you can't perform, and only when the task beats the sub-agent's overhead. If the environment hides the model/effort, write `Model : current agent @ effort:unavailable` and don't claim switching.

Map the provider-neutral tiers as:

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

Before each phase, load `agents/sage/roles/role-<lens>.md`; if missing, create it in the **`AGENTS.md` §2 role format** (Expertise + Pitfalls + How I work — concrete, not a motivational bio). Output `Role: <lens> [loaded|created]`, and on handoff `Role: <next> [loaded] — handoff from <prev>`.

---

## Step 1 — Load roles

Select the role(s) from the detected signals and stack, load or create the role files, output the role lines before the phase that uses them, and hand off roles explicitly when the phase changes.

---

## Step 2 — Read knowledge and reusable assets

**Step 2a — project knowledge.** Open `agents/sage/<domain>/index.md`, its `context.md` glossary when present, `rules.md`, and relevant `decisions/*.md`. Quote only the rules that apply, challenge conflicting terminology, and respect each rule's `enforcement` (`block` = must/never · `warn` = strong preference · `advise` = guidance — see `AGENTS.md` §5). If the domain folder or rules file is missing, say so and continue; create knowledge only through the command that owns it or in Step 4.

**Step 2b — reusable assets.** Search for existing utilities, hooks, components, services, commands, validators, schemas, fixtures, generated clients, migrations, test helpers, CI jobs, deploy scripts, and runbooks before writing new ones. When you find one, **open the source file and read its exports / public API / command behavior** — never infer from a name, README, or decision file. Report only the assets that matter.

**Keep these scans out of main context.** When the knowledge folder or reuse surface is large, run Steps 2a–2b in a **sub-agent** (Explore / Task) and take back only the findings — the rules that apply and the exports you'll reuse, not the raw file dumps. You pay for the conclusion, not every file, and independent scans run in parallel. For a small repo, read inline — a sub-agent isn't worth the overhead.

**Step 2c — confirm and execute the route.** State the chosen route and why. For
`foggy-single-session`, run `/sage-grill` even when `plan-flow` is unchecked. For
`large-multi-session`, run `/sage-wayfinder` and stop this implementation run
until its map produces a spec-ready handoff. Continue directly only for
`clear-single-session` or after a command returns its explicit clear exit state.

---

## Step 3 — State intent and plan before writing

Apply the complete risk policy and driver-control matrix in **`AGENTS.md` §1.4**;
do not reproduce or loosen it here. Output the intent block before making changes.
LOW may proceed when bounded. MEDIUM may `warn` and proceed only when reversible
and fully controlled; unresolved scope/contract/rollback decisions use `ask`.
HIGH always uses `ask` before file changes — neither `mode:auto` nor a general
autonomous request is an approval for a named HIGH-risk target/effect.

```text
Repo    : <repo-root>
Role    : <role> — <one-line task summary>
Model   : <model or current agent> @ effort:<effort or unavailable>
Intent  : <what this change will do>
Touches : <files, systems, domains affected>
Risk    : LOW | MEDIUM | HIGH · confidence:<low|medium|high> — <why>
Drivers : <affected asset → concrete failure mode>
Controls: <required control → planned command/evidence>
Decision: proceed | warn | ask | reject
```

`proceed` = safe to continue · `warn` = continue but name a caveat · `ask` = need approval/info before changing files · `reject` = unsafe or impossible.

**Consume the route handoff; do not re-interview.** `/sage-grill` owns product
intent, canonical terminology, scope, and product trade-offs. `/sage-wayfinder`
owns multi-session decision coordination. `/sage-flow` owns implementation
design against real code/schema. If new code evidence contradicts a resolved
decision, reopen that named decision with the evidence; never ask the same
question again merely because a new command started.

**Step 3a — plan.** Identify parallel vs sequential work; annotate each task with owner role, tier (`fast`/`standard`/`deep`), effort if available, dependency, and expected validation. Every required risk control must have an owning phase and expected evidence.

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

**Step 3b — progress.** Mark task starts/completions as they happen; report results without waiting for the whole phase. On a failure that affects correctness, report immediately and pause. For non-blocking failures, continue only if the remaining path is safe and say why. A new driver, wider target, or destructive effect invalidates the old assessment: stop the affected phase, reassess, add controls, and renew approval if the envelope changed.

---

## Write the code

Keep changes scoped to the intent; reuse existing assets first; follow project naming/folder conventions; avoid unrelated cleanup and broad rewrites unless the plan approved them; preserve public contracts unless intentionally changing them; keep frontend/backend contracts aligned; protect data integrity and migration safety; keep the generated-code source of truth clear; add tests when `unit-test`/`e2e-test` applies; update docs only when behavior, setup, API, public usage, configuration, deployment, or team decisions changed.

---

## Universal validation rules

Validation is mandatory, but exact commands depend on the detected stack. Prefer commands already defined in the repo. Run the closest relevant checks **plus every applicable required control declared under `AGENTS.md` §1.4**:

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

If a check or required control is unavailable, state the exact missing evidence
and consequence; do not mark it passed. Use the actual evidence to reassess
residual risk, lowering the initial level only when likelihood/exposure fell or
reversibility improved. Documentation is required only when the change affects
external behavior, setup, deployment, API contracts, public flows,
configuration, team decisions, or reusable patterns; otherwise say why docs
were skipped.

---

## Step 4 — Capture knowledge

Knowledge always goes to `agents/sage/` inside the active repo. Never store project knowledge in local memory, a scratch file, or another repo.

**Gate first — don't burn the analysis when there's nothing to learn.** Run the extraction below only when the change actually produced something transferable: a design decision, a human correction, a stated "always / never", a non-obvious gotcha. A mechanical edit or typo produces nothing — output one line, `Knowledge · [none] <file> — nothing transferable this run`, and skip the rest. Otherwise analyze the whole run, then split by topic. Review the conversation, files created/changed, validation results, and corrections, and capture **every distinct transferable pattern that clears the noise bar** (`AGENTS.md` §3: hard to reverse, non-obvious, or a genuine trade-off) — a real run may produce more than one (architecture boundary, naming convention, validation rule, library gotcha, testing pattern, security rule, migration pattern, deployment rule, performance constraint). **Do not reduce multiple patterns into one vague summary, and do not capture obvious defaults.** Every run outputs one of:

- **A — New knowledge (one file per idea):** `agents/sage/<domain>/decisions/<slug>.md` (frontmatter format in `AGENTS.md` §2). Write the **pattern**, not the implementation. Good: "Forms must use the shared resolver so client and server validation stay aligned." Bad: "Fixed CreateUserForm.tsx by adding valibotResolver." Two unrelated patterns = two files, in the correct domains. `status: proposed`, `source: ai`, sensible `enforcement`.
- **B — Updated knowledge:** update the existing file in place when it was relevant but incomplete, stale, or corrected by this run.
- **C — No new knowledge:** only when nothing transfers. State it: `Knowledge · [none] agents/sage/<domain>/rules.md — Existing rules fully covered this case.` Silence is not allowed.

---

## Step 5 — Summary

Close with the summary block defined in **`AGENTS.md` §4b** (the debugger vs. build/implementation template), **scaled to risk** — a LOW-risk or mechanical change gets a two-line recap (`Done` + `Validated`), not the full block. Do not redraw the template here; §4b is the single source.

Beyond §4b's fields, this command always adds these rows to the block (complete sentences, concrete files/commands):

- **Model** · `<model or current agent> @ effort:<effort or unavailable>`
- **Changed** · `<file>` — what changed and why (one row per file)
- **Validated** · the exact command/check → passed | failed | skipped with the reason; never "looks correct"
- **Residual risk** · `<LOW | MEDIUM | HIGH>` — evidence that reduced it, or the control gap that remains
- **Docs** · updated path, or skipped with the exact reason
- **Remaining** · known limitation, follow-up, or "None"

---

## Stop conditions

Use `AGENTS.md` §1.4 and §4 as the single source for risk gates. In particular,
stop before file changes for every HIGH assessment and obtain explicit approval
for its named target/effect; `mode:auto` or a general autonomous request is not
that approval. Also stop for destructive/overwrite scope, ambiguous sensitive
boundaries, missing contracts/schemas/migration history that could hide HIGH
impact, failed critical controls, or unsafe requests. Do not stop for trivial
preferences when a bounded LOW/MEDIUM best effort is available — state the
assumption and continue.

---

## Common anti-patterns

Avoid: showing the checklist for a pure question; hiding choices instead of labeling them; depending only on a proprietary picker some tools cannot render; using old mode names `smart`/`always` in new config; saying "AskUserQuestion" when the environment lacks it; assuming JavaScript/TypeScript/web without reading repo indicators; claiming provider-specific models in an unknown-provider environment; raising effort above the session ceiling or downgrading `plan-flow` below it; treating risk as a header-only label; deriving every control from LOW/MEDIUM/HIGH instead of the driver; treating `mode:auto` as HIGH-risk approval; lowering residual risk without evidence; treating validation as optional or ending with "looks good"; broad unrelated cleanup; updating docs for every tiny edit; writing one vague knowledge file for multiple decisions.

---

## Minimal completion checklist

Before the final response, confirm internally: the request was classified correctly; pure questions skipped the checklist; code requests read/created `.sage-local.json` (old `askMode` migrated to `mode`); mode was `auto` or `ask`; all five choices stayed visible with a recommendation label + reason; role files were loaded/created; rules and assets were checked; the repo stack was detected from real files; risk drivers, confidence, required controls, verdict, and plan were stated with provider-neutral tiers within the ceiling; controls had owners and evidence; changes stayed in scope; validation ran or a gap was reported with its consequence; residual risk followed from evidence; docs updated or skipped with a reason; Step 4 knowledge was new/updated/none, split by topic; Step 5 summary included Changed, Decisions or Fix, Validated, Residual risk, Docs, Remaining, and Knowledge.
