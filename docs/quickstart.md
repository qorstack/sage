# Quick start

Get Knowai running with Claude Code in 5 minutes.

## 1. Install

Pick one:

```bash
# Via uv (recommended)
uv tool install knowai

# Via pipx
pipx install knowai

# Or run without installing (one-shot)
uvx knowai scan .
```

Requires Python 3.11+.

## 2. Verify

```bash
knowai --version
knowai scan .
```

You should see a summary: language, framework, architecture, domains, conventions.

## 3. Connect to Claude Code

```bash
claude mcp add knowai -- uvx knowai mcp --repo .
```

Or edit `.claude/settings.json` manually:

```json
{
  "mcpServers": {
    "knowai": {
      "command": "uvx",
      "args": ["knowai", "mcp", "--repo", "."]
    }
  }
}
```

Restart Claude Code. You should see 20 Knowai tools available.

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
knowai memory decide auth \
  "Use SendGrid for password reset emails" \
  --body "Primary: SendGrid. Fallback: AWS SES. Templates in templates/auth/."
```

Now any future `analyze_intent` for auth-related work will surface this memory to Claude.

## 6. (Optional) Set up a multi-repo workspace

If your product spans multiple repos, Knowai treats one of them as the **knowledge home** (the "shared brain") and auto-links the rest.

### Recommended layout

```text
~/code/myproduct/
  myproduct-knowledge/   ← workspace home (workspace.toml, memory.json live here)
  myproduct-api/         ← backend (working repo)
  myproduct-web/         ← frontend (working repo)
```

Naming convention: the knowledge repo's folder name ends with `-knowledge`. Knowai uses this to auto-derive the workspace name (strips `-knowledge` and `-knowai` suffixes).

### Tech lead — initialize the workspace home

```bash
mkdir -p ~/code/myproduct/myproduct-knowledge && cd ~/code/myproduct/myproduct-knowledge
git init   # or: git clone <empty-team-repo> .
knowai init
```

This creates `workspace.toml`, `packs/`, `scans/` in the folder and registers the path in `~/.knowai/registry.toml`. Push to a shared remote so teammates can clone it.

### Each dev — link a working repo

```bash
cd ~/code/myproduct/myproduct-api
knowai init
```

That's it. Knowai auto-detects the `-knowledge` sibling, reads its git remote, writes a 2-line `.knowai/config.toml`, and auto-registers this repo in the workspace's `workspace.toml`.

### Joining from a fresh machine

```bash
cd ~/code/myproduct
git clone <team-knowledge-repo-url> myproduct-knowledge
git clone <team-api-repo-url>       myproduct-api
cd myproduct-api && knowai init    # auto-links via the sibling
```

Memory + decisions + approvals are now shared across all linked repos. To share with your team, see [git-sync.md](git-sync.md).

### Override auto-detection

```bash
knowai init --knowledge --name myproduct   # force this folder to be the workspace home, custom name
knowai init --link myproduct --remote <git-url>   # force link mode (no sibling needed)
```

## Next

- [CLI reference](cli.md) — full command list
- [MCP integration](mcp.md) — detailed Claude/Cursor/Cline setup
- [Usage examples](usage-examples.md) — 7 real-world scenarios
