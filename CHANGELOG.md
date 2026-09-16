# Changelog

All notable changes to Sage. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.7.0] — 2026-09-16

### Added

- A plain-language landing page guide now shows how `/sage` routes clear,
  unclear, and multi-session work, plus the full Grill → Flow → Ticket → Build
  → Review journey.

### Changed

- Redesigned the landing page as an engineering decision ledger, with a visible
  Sage decision trace, clearer installation flow, responsive layouts, keyboard
  focus states, and reduced-motion support.

## [1.6.0] — 2026-09-08

### Added

- Flow workspaces now keep each effort's Grill spec, Flow design, implementation
  tickets, and indexed debug evidence together under
  `agents/sage/flows/<slug>/`. Relevant screenshots are embedded into updated
  Markdown with relative links.

### Changed

- Visual debugging now captures the smallest useful before/after evidence first
  and reuses it before loading full browser state. Full-state debugging is
  reserved for evidence that remains ambiguous and unresolved race,
  auth/session, or cross-service mechanisms.
- Existing flat flow artifacts are not bulk-migrated. Sage discovers them for
  backward compatibility and migrates an artifact on its next material update,
  leaving a pointer at the legacy path. Installer-managed reference flows remain
  flat and user flow workspaces remain untouched by updates.

## [1.5.0] — 2026-09-05

### Changed

- Test authoring is now explicit opt-in. `/sage` no longer recommends, selects,
  plans, or invokes unit/E2E test creation; new tests are written only through
  `/sage-unit-test`, `/sage-e2e-test`, or an equivalent direct request. Running
  the repository's existing tests remains part of validation.

## [1.4.0] — 2026-08-25

### Added

- **`/sage-ticket`** — cuts `requirements-clear` / `design-clear` work into
  ordered **implementation** tickets in `agents/sage/flows/<slug>-tickets.md`,
  each a single verifiable outcome sized for one session with dependencies,
  when → then acceptance criteria, its owed risk controls, and the exact
  validation command. It then works the frontier, claiming and building one
  ticket at a time. It refuses foggy input and routes it back to `/sage-grill`
  or `/sage-wayfinder`. Wayfinder keeps sole ownership of **decision** tickets;
  the two backends are never mirrored.
- **`/sage-review`** — the correctness and requirement-conformance review Sage
  was missing. It resolves the target (named paths → branch diff → working
  tree), reviews against the tickets, flow, spec, and matched rules, covers
  conformance, correctness, edge cases, contracts, state lifecycle, owed
  controls, reuse, and simplicity, then adversarially refutes each finding
  before reporting it as CONFIRMED or PLAUSIBLE. Read-only: fixes go back
  through `/sage`, security findings to `/sage-security-review`, product
  questions to `/sage-grill`.
- Thin adapters for both commands across Claude Code, Codex, Cursor, GitHub
  Copilot, Gemini CLI, Windsurf, and Cline.

### Changed

- `/sage-grill` now handles a human-supplied document (PRD, ticket, API
  contract, transcript) explicitly: read it in full, treat every statement as a
  claim to verify against the repo, and grill what it contradicts, leaves
  undefined, or never mentions. It also routes its handoff by what remains
  undecided — `/sage-flow` when implementation decisions are open, straight to
  `/sage-ticket` when only the build remains.
- `/sage-flow`'s Build checklist items now carry a stable id, owning system,
  dependencies, and a when → then acceptance condition, so `/sage-ticket` has a
  sliceable contract to consume instead of bare checkboxes.

## [1.3.0] — 2026-08-20

### Changed

- **`/sage-e2e-test` now owns the full autonomous E2E loop** — it prioritizes
  high-value journeys, explores real UI behavior when browser control exists,
  records expectations before implementation, runs targeted tests continuously,
  classifies failures as test/application/environment issues, and completes only
  with repeatable evidence and explicit residual risk.
- Model routing is provider-neutral with an optional Codex mapping: Terra for
  coordination, Luna for bounded mechanical work, and Sol for unresolved complex
  work when available within the session ceiling. Other agents keep the same
  workflow without requiring Codex model names, subagents, or `@Chrome`.
- Routine scope, retry, save, and framework choices now resolve from repository
  evidence instead of forcing an “ask before running” checkpoint. Material
  production, credential, destructive, side-effect, and business decisions remain
  gated by the central Sage risk policy.

## [1.2.0] — 2026-08-19

### Added

- **`/sage-refactoring-code`** — a standalone, stack-agnostic skill for writing
  and refactoring readable application code, components, functions, utilities,
  modules, and database schemas. It follows clear project vocabulary without
  copying accidental complexity, reduces unnecessary nesting and speculative
  abstraction, and preserves correctness, security, data integrity, and public
  behavior before simplifying.
- Thin adapters expose the skill across Claude Code, Codex, Cursor, GitHub
  Copilot, Gemini CLI, Windsurf, and Cline. Codex also receives a discoverable
  `$sage-refactoring-code` skill package.

### Fixed

- Restored the canonical `plan-flow` recommendation boundary in `AGENTS.md`,
  keeping routine multi-file work, ordinary bugs, and dependency changes from
  triggering flow design solely because of their category.

## [1.1.0] — 2026-08-06

### Added — cognition upgrades

- **Project DNA architecture specification** — defines Sage's preparation-first
  cognition data plane: evidence-backed DNA facets, progressive L0–L4 retrieval,
  source-fingerprint freshness, incremental invalidation, hierarchy/inheritance,
  tool contracts, human-governed knowledge, compatibility gates, and a phased
  delivery plan. This is explicitly specification only; the shipped release
  remains the Markdown protocol until the runtime passes its acceptance gates.
- **Manifest-driven safe installer** — Bash and PowerShell now preflight and
  install the same exact Sage-owned asset list, including Project DNA and
  protocol flows. Adapter cleanup uses an append-only exact basename manifest
  instead of deleting every `sage*` file, so custom knowledge, flows, docs,
  local config, and unrelated adapter files survive fresh installs and upgrades.
- **Run-until-gate interaction policy** — version 3 separates checklist mode
  from continuation. The parent `/sage` now consumes Grill/Flow/Wayfinder
  handoffs and completes every unblocked frontier wave until a material
  human/safety/access gate or true completion; `strict` keeps command
  checkpoints when explicitly preferred.
- **Capability-aware checklist picker** — `mode:auto` never asks for checklist
  input. `mode:ask` prefers a native multi-select, falls back to a structured
  Recommended/Defaults/Customize choice, then to compact keyword/exception
  input when the host has no picker.
- **Role status and boundary** — committed roles are `approved`, newly generated
  roles start `proposed`, and role files contain expertise/failure modes rather
  than duplicated approval gates or version/path facts.
- **Three-route dispatcher** — every code request is classified as
  `clear-single-session`, `foggy-single-session`, or `large-multi-session` before
  design; Grill/Wayfinder guards are independent of the locked checklist.
- **`/sage-wayfinder`** — local-first durable maps and decision tickets with
  destination, fog, out-of-scope, repeated frontier waves, blocking, claim,
  HITL/AFK types, and spec handoff; configured issue trackers remain optional
  backends.
- **Grill-with-docs behavior** — `/sage-grill` now updates domain context inline,
  checkpoints multi-decision sessions before questioning, stress-tests material
  decisions with scenarios, and has an explicit no-repeat handoff to Flow.
- **Operational risk controls** — Sage now identifies concrete risk drivers,
  assigns mandatory driver-specific controls, records validation evidence, and
  reports residual risk. `mode:auto` no longer has any ambiguous path around a
  HIGH-risk, destructive, HITL, or matched-`block` gate.
- **`/sage-grill`** — a new command that interrogates a foggy request into agreed
  decisions (batching independent questions while keeping dependent branches
  one-at-a-time; facts are looked up by the agent) before `/sage-flow`. The
  grilling technique is
  adapted from [Matt Pocock's skills](https://github.com/mattpocock/skills)
  (`grilling`, MIT), folded into Sage's pipeline rather than shipped standalone.
- **Large-effort decision-map** in `/sage-flow` — when an effort is too big for
  one pass, chart the open decisions (sharp ones only) before building; plus an
  explicit `Out of scope` list and "flow produces decisions, not deliverables".
- **Sub-agent offload** for the read-heavy scans (knowledge + reuse) — run them in
  a sub-agent and take back only the findings, keeping main context lean.

### Changed — honesty, token cost, and less drift

- **Ikigai removed from the reply header**; role files now use **Expertise +
  Pitfalls + How I work** (concrete strengths and blind spots, not a bio).
- **`auto-switch-model` reframed honestly** — the session model + effort is a hard
  ceiling on **cost**, not just capability. You cannot change the running session
  model; "switching" means picking the effort tier and pushing a down-shiftable
  sub-task to a smaller/cheaper sub-agent — only downward, never a switch you
  can't perform.
- **Knowledge capture is trigger-gated + noise-barred** — skip the analysis when a
  run produced nothing transferable; capture only what is hard to reverse,
  non-obvious, or a genuine trade-off. Summary block **scales to risk**; knowledge
  reading is **index-first**. All to cut both knowledge rot and token cost.
- **Deduped `AGENTS.md` ↔ `commands/sage.md`** — `AGENTS.md` owns the protocol;
  the command file keeps only its operational tables and points to `AGENTS.md`
  where they overlap (a source-of-truth note now guards against future drift).

### Changed — pivot to a single-file protocol

- **Sage is now a single `AGENTS.md` cognition protocol** plus a Markdown
  knowledge tree at `agents/sage/`. No install, no server, no Python, no MCP.
- Added `integrations/` — thin per-agent adapters (Cursor, Windsurf, Cline,
  Copilot, Gemini/Antigravity) that route each tool to `AGENTS.md`; Claude Code,
  Codex, OpenCode, and Antigravity read it natively.
- **Removed** the entire Python implementation (MCP server, CLI, memory stores,
  reasoning engine, scanner, graph, web dashboard, cognition packs), packaging,
  Docker, and the Python CI workflows. Recoverable from git history.
- Rewrote README, llms.txt, CLAUDE.md, CONTRIBUTING, ROADMAP, and the landing
  install flow around "copy one file."

### Previously (Python implementation — now removed)

### Added — concurrency & safety

- `storage` package — cross-platform file lock (`fcntl` POSIX / `msvcrt` Windows), atomic write (write-temp-then-rename), and `read_modify_write()` helper
- `FileMemoryStore` uses atomic R-M-W on every save — no lost updates when multiple Claude/CLI sessions write simultaneously
- `ApprovalQueue` same treatment — concurrent submits/approves/rejects are serialized
- **Approve/reject fail-safe**: once REJECTED, an approval stays rejected. Subsequent `approve()` is a no-op. `auto_merge_json` enforces the same rule in git sync conflicts.

### Added — memory schema v2 (auto-migrated from v1)

New shape:

```json
{
  "version": 2,
  "entries": {"<id>": {...}},
  "syntheses": {"<domain>": {summary, key_themes, open_questions, stale, ...}}
}
```

- Per-domain synthesis cache — AI reads raw entries, distills themes, calls `save_synthesis()` once; future sessions reuse cached synthesis
- Synthesis auto-marked `stale: true` when a new entry arrives → triggers re-synthesis
- v1 flat-dict files auto-migrate on first read

### Added — delegate-to-Claude MCP tools (no LLM inside Sage)

- `get_domain_knowledge(domain)` — raw entries + cached synthesis + instruction to AI
- `save_synthesis(domain, summary, themes, questions)` — AI caches its own synthesis
- `assess_risk_in_context(request)` — rule-based risk + historical incidents; AI may UPGRADE only
- `get_module_context(module_path)` — signals for AI judgment about module criticality

### Added — risk upgrade-only enforcement

- `analyze_intent` returns a `risk_policy` field: Sage's decision is authoritative; AI may stricten (`proceed → warn → ask → reject`) but never loosen

### Added — distributed knowledge (Phase 4.A)

- `paths` module — cross-platform central path resolver (`~/.sage/`, honors `PRECEPT_HOME`)
- `link` module — per-repo `.sage/config.toml` + walk-up workspace resolver
- CLI: `workspace create`, `workspace list`, `link`, `unlink`, `migrate`
- `load_central(workspace_name)` for loading workspace config from central store

### Added — install & onboarding

- `install.sh` / `install.ps1` — one-line bootstrap (installs uv if missing, installs sage, optional workspace + Claude registration)
- `sage init --link <workspace>` — auto-detect role + domains + create link config
- README rewritten with copy-paste examples for Claude Code / Cursor / Cline / Continue / Windsurf / no-AI usage

### Changed

- `create_store()` and `get_queue()` auto-resolve central workspace when a link config is present (fully backward compatible)
- `workspace.config_loader.load()` falls back to central path when no local `sage.toml`
- Documentation restructured for OSS audience (`docs/` user-facing, `internal/` design specs)
- `CONTRIBUTING.md`, `ROADMAP.md`, `CHANGELOG.md` at repo root

## [0.3.0] — 2026-Q1

### Added

- Multi-repo workspace via `sage.toml`
- `WorkspaceScanner` with parallel repo scanning
- `CrossRepoImpactAnalyzer`
- `GraphExporter` (React Flow JSON, Mermaid, DOT)
- `ApprovalQueue` with pending/approved/rejected states
- 8 MCP tools for workspace + graph + approval

## [0.2.0]

### Added

- `FileMemoryStore` (default, zero dependencies)
- `QdrantMemoryStore` (optional, semantic search) with graceful fallback
- Human approval workflow for memory entries
- 7 built-in cognition packs (auth, otp, payment, webhook, order, notification, worker)
- 6 memory + pack MCP tools
- PyPI packaging

## [0.1.0]

### Added

- Initial release
- Scanner: language/framework/architecture/domain/conventions/assets
- `CognitiveGraph` with cascade rules
- Intent + Impact + Risk analyzers
- `ReasoningEngine`
- 8 cognitive MCP tools
- Typer CLI: `scan`, `analyze`, `impact`, `conventions`, `assets`
- FastAPI REST API (Phase 1 routes)
