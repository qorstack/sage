# Changelog

All notable changes to Knowlyx. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `paths` module — cross-platform central path resolver (`~/.knowlyx/`, honors `KNOWLYX_HOME` env)
- `link` module — per-repo `.knowlyx/config.toml` + walk-up workspace resolver
- CLI: `workspace create`, `workspace list`, `link`, `unlink`, `migrate`
- `load_central(workspace_name)` for loading workspace config from central store
- Tests: `test_paths.py`, `test_link.py`
- Documentation restructured for OSS audience (`docs/` user-facing, `internal/` design specs)
- `CONTRIBUTING.md`, `ROADMAP.md`, `CHANGELOG.md` at repo root

### Changed

- `create_store()` and `get_queue()` now auto-resolve central workspace when a link config is present (fully backward compatible)
- `workspace.config_loader.load()` falls back to central path when no local `knowlyx.toml` found

## [0.3.0] — 2026-Q1

### Added

- Multi-repo workspace via `knowlyx.toml`
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
