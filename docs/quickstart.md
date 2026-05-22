# Quick start

Get Knowlyx running with Claude Code in 5 minutes.

## 1. Install

Pick one:

```bash
# Via uv (recommended)
uv tool install knowlyx

# Via pipx
pipx install knowlyx

# Or run without installing (one-shot)
uvx knowlyx scan .
```

Requires Python 3.11+.

## 2. Verify

```bash
knowlyx --version
knowlyx scan .
```

You should see a summary: language, framework, architecture, domains, conventions.

## 3. Connect to Claude Code

```bash
claude mcp add knowlyx -- uvx knowlyx mcp --repo .
```

Or edit `.claude/settings.json` manually:

```json
{
  "mcpServers": {
    "knowlyx": {
      "command": "uvx",
      "args": ["knowlyx", "mcp", "--repo", "."]
    }
  }
}
```

Restart Claude Code. You should see 20 Knowlyx tools available.

## 4. Try a cognition request

In Claude Code, ask anything that touches code. Example:

> add password reset flow

Claude will call `analyze_intent` first and return a structured report with:

- Detected domain + action
- Inferred requirements (token expiry, rate limit, audit log)
- Affected files + cascade risks
- Risk decision (proceed / warn / ask / reject)
- Reusable assets to import instead of recreating
- Cognition pack for the domain
- Any approved memory entries the team has saved

Claude writes code that respects everything in that report.

## 5. (Optional) Save your first team decision

```bash
knowlyx memory decide auth \
  "Use SendGrid for password reset emails" \
  --body "Primary: SendGrid. Fallback: AWS SES. Templates in templates/auth/."
```

Now any future `analyze_intent` for auth-related work will surface this memory to Claude.

## 6. (Optional) Set up a multi-repo workspace

If your product spans multiple repos, Knowlyx treats one of them as the **knowledge home** (the "shared brain") and auto-links the rest.

### Recommended layout

```text
~/code/myproduct/
  myproduct-knowledge/   ← workspace home (workspace.toml, memory.json live here)
  myproduct-api/         ← backend (working repo)
  myproduct-web/         ← frontend (working repo)
```

Naming convention: the knowledge repo's folder name ends with `-knowledge`. Knowlyx uses this to auto-derive the workspace name (strips `-knowledge` and `-knowlyx` suffixes).

### Tech lead — initialize the workspace home

```bash
mkdir -p ~/code/myproduct/myproduct-knowledge && cd ~/code/myproduct/myproduct-knowledge
git init   # or: git clone <empty-team-repo> .
knowlyx init
```

This creates `workspace.toml`, `packs/`, `scans/` in the folder and registers the path in `~/.knowlyx/registry.toml`. Push to a shared remote so teammates can clone it.

### Each dev — link a working repo

```bash
cd ~/code/myproduct/myproduct-api
knowlyx init
```

That's it. Knowlyx auto-detects the `-knowledge` sibling, reads its git remote, writes a 2-line `.knowlyx/config.toml`, and auto-registers this repo in the workspace's `workspace.toml`.

### Joining from a fresh machine

```bash
cd ~/code/myproduct
git clone <team-knowledge-repo-url> myproduct-knowledge
git clone <team-api-repo-url>       myproduct-api
cd myproduct-api && knowlyx init    # auto-links via the sibling
```

Memory + decisions + approvals are now shared across all linked repos. To share with your team, see [git-sync.md](git-sync.md).

### Override auto-detection

```bash
knowlyx init --knowledge --name myproduct   # force this folder to be the workspace home, custom name
knowlyx init --link myproduct --remote <git-url>   # force link mode (no sibling needed)
```

## Next

- [CLI reference](cli.md) — full command list
- [MCP integration](mcp.md) — detailed Claude/Cursor/Cline setup
- [Usage examples](usage-examples.md) — 7 real-world scenarios
