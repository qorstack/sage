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

If your product spans multiple repos:

```bash
knowlyx workspace create my-product
cd ~/code/api && knowlyx link my-product --role backend --critical
cd ~/code/web && knowlyx link my-product --role frontend
```

Memory + decisions are now shared across all linked repos. To share with your team, see [git-sync.md](git-sync.md).

## Next

- [CLI reference](cli.md) — full command list
- [MCP integration](mcp.md) — detailed Claude/Cursor/Cline setup
- [Usage examples](usage-examples.md) — 7 real-world scenarios
