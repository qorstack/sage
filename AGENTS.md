# AGENTS.md — Precept for AI agents

Guidance for AI coding agents (Claude Code, Cursor, Cline, etc.) installing,
setting up, or integrating **Precept**. Read this before deciding whether and
how to use it.

## Copy-paste setup prompt

Want your AI to set everything up? Paste this to your agent — it leans on the
rest of this file, so there's nothing to repeat:

> Set up **Precept** on this machine so coding agents consult it before writing
> code. (1) Install the CLI: `uv tool install --force git+https://github.com/qorstack/preceptai.git`.
> (2) **Make a dedicated folder for the stack** (e.g. `~/precept`) and run
> `precept quickstart` **inside it** — it writes `.env` + `docker-compose.yml`
> **into that folder**, starts Postgres + the dashboard there via Docker,
> registers the MCP server globally with Claude Code, and installs the `/precept`
> slash commands. (3) **Verify**: the dashboard answers at
> `http://localhost:9080` and `claude mcp list` shows `precept ✓`. (4) In a real
> project repo, add a `precept.config` (`workspace` + `repo_name`) and run
> `/precept-generate` once to seed team memory. If any step fails, read the
> error, fix the root cause, retry, and report what you changed.

## What it is

Precept is a **cognitive enforcement layer**, not another coding agent. It sits
between your agent and your repo over MCP, and forces the agent to *understand*
a change — business logic, blast radius, reusable assets, team decisions —
**before** it writes code. It returns a binding verdict: `proceed / warn / ask /
reject`. Reasoning is rule-based (no LLM, deterministic, no API key). It works
*alongside* the agent you already use; it does not replace it.

## Install + set up (one command)

```bash
uv tool install --force git+https://github.com/qorstack/preceptai.git
mkdir -p ~/precept && cd ~/precept   # a dedicated home for the stack
precept quickstart                   # safe to re-run; --force to update
```

### What `precept quickstart` creates, and WHERE

This is the part people miss — there are three different locations:

| Thing | Where it lands | Notes |
| --- | --- | --- |
| `.env` + `docker-compose.yml` | **the folder you run `quickstart` in** (CWD) | The Postgres + dashboard stack lives here. `cd` back here to run `docker compose ...`. |
| Postgres + dashboard containers | Docker (`precept-postgres`, `precept-web`) | Dashboard → `http://localhost:9080`, Postgres host port `55432`. |
| MCP server registration | Claude Code **user config** (global) | Available in *every* repo, not just this folder. |
| `/precept`, `/precept-generate` | `~/.claude/commands/` | Global slash commands. |

So: run `quickstart` **once**, from a folder you'll remember (not a throwaway
directory). The MCP server and slash commands are global; only the stack files
are tied to that folder.

Cross-platform (Windows / macOS / Linux). A preflight locates Docker and Claude
Code even when they're installed but missing from `PATH`. Re-run with
`precept quickstart --force` to update: it pulls the latest image, re-registers
MCP, and reinstalls the commands (your `.env` is preserved).

## How an agent uses it (the mandatory workflow)

Before ANY code change, call the MCP tools in this order:

1. `analyze_intent(request)` — **first, always.** Returns domain, impact, risk,
   the `proceed/warn/ask/reject` decision, and any team skills/memory to read.
2. `get_reusable_assets(domain)` — reuse what exists; don't reinvent.
3. `assess_risk_in_context(request)` — you may make the verdict *stricter* using
   team memory; never looser.
4. `validate_generated_code(code)` — before writing. Fix blockers, re-validate.

Honor the verdict: **`reject` → stop. `ask` → pause for a human** (call
`request_approval` and wait). Never auto-proceed past these.

In Claude Code, the `/precept <request>` slash command makes this consult
mandatory (a plain prompt can slip past the pipeline).

## Team knowledge (the differentiator)

Precept memory is **team-shared and human-approved**, not personal:

- When the dev states a team rule/decision, capture it without being asked —
  `save_skill(...)` for multi-rule guidance, `remember_team_decision(...)` for a
  single decision, `remember_business_context(...)` for context needing human
  ratification.
- AI-written memory lands as **Pending** until a human approves it on the
  dashboard (`http://localhost:9080`). Approved entries git-sync to the team.
- **Diff before every write**: call `recall_context` / `list_memory` /
  `read_skill` first. Update the same entry in place if stale; don't duplicate.

## Use with non-Claude agents

Precept is a standard stdio MCP server — the command is always `precept mcp`.
Print the exact config for your client:

```bash
precept mcp-config cursor      # or: claude · vscode · windsurf · cline · all
```

Generic config most clients accept:

```json
{ "mcpServers": { "precept": { "command": "precept", "args": ["mcp"] } } }
```

## Gotchas

- The per-repo config file is named **`precept.config`** (exactly — not
  `precept-ai.config`). It declares `workspace` + `repo_name`; without it, AI
  memory falls back to `global` scope instead of your workspace.
- `quickstart` never clobbers existing `.env` / `docker-compose.yml` — use
  `--force` to refresh the compose file and pull the latest image.
- Ports are non-standard on purpose (dashboard `9080`, Postgres `55432`) to
  avoid clashing with anything already on `8080` / `5432`.
- Verdicts are advisory until wired into CI / a pre-commit hook — see the README
  "Enforce it" section for the hard gate (`precept check --strict`, exit codes
  `0/1/2`).

## Pointers

- [README.md](README.md) — full human guide (manual setup, enforcement, dashboard tour).
- [`precept mcp-config`](README.md#works-with-any-ai-agent-mcp) — per-client MCP setup.
- `/precept-generate` — seed team memory from a repo (run once per repo).
- Dashboard — `http://localhost:9080` (approve memory, browse knowledge, audit log).
- Source — https://github.com/qorstack/preceptai
