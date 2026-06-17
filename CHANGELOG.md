# Changelog

All notable changes to Sage. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
