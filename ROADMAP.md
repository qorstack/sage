# Roadmap

High-level milestones. For detailed design specs, see [`internal/`](internal/).

## Released

### v0.1 — System Understanding ✅

Scanner, conventions detector, reusable asset detector, cognitive graph, intent + impact + risk analyzers, reasoning engine, 8 MCP tools, CLI.

### v0.2 — Memory + Cognition Packs ✅

File-based memory store, Qdrant fallback, human approval workflow, 7 built-in cognition packs (auth, otp, payment, webhook, order, notification, worker), 6 memory MCP tools.

### v0.3 — Workspace + Graph + Approval ✅

`knowai.toml` multi-repo workspace, cross-repo impact analyzer, graph exporter (React Flow / Mermaid / DOT), approval queue, 8 workspace MCP tools.

### v0.4 — Distributed Knowledge ✅

Central knowledge store at `~/.knowai/workspaces/`, per-repo link config, auto-resolver, migration script. Dev clones one repo at a time and still gets shared memory + decisions.

## In progress

### v0.5 — Sync + Self-Review + Hooks 🟡

- Git sync CLI wrapper (`knowai sync init/pull/push`)
- AI self-review (`validate_generated_code` MCP tool — block bad code before write)
- Commit-time enforcement (`knowai commit-check` + pre-commit hook)
- `knowai init` auto-scaffold
- Complete REST API for memory/workspace/approval
- GitHub Actions CI

## Planned

### v0.6 — Workspace-aware analysis

Persistent scan cache so AI can answer cross-repo questions even when only one repo is cloned locally.

### v0.7 — Design Cognition

Detect design tokens, component patterns, spacing scales — block AI from breaking the design system.

### v1.0 — Frontend UI

Next.js + React Flow app for visualizing cognitive graph, browsing memory, managing approval queue.

## Speculative / Phase 2

- ML-based risk scoring (trained on historical incidents)
- Local LLM augmentation via Ollama (auto-extract memory from PRs)
- Knowai Cloud (managed sync + web UI for larger teams)
- Business conflict detection (feature ↔ policy)
- Auto-extracted decisions from PR descriptions

## How to influence the roadmap

Open a [GitHub Discussion](https://github.com/qorstack/knowai/discussions) — concrete use cases drive priority more than feature requests.
