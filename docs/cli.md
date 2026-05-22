# CLI reference

Every Knowlyx command. Run `knowlyx --help` for live help.

## Project commands

### `scan`

Scan a repo and show its cognitive profile.

```bash
knowlyx scan [path]
knowlyx scan . --json
```

### `analyze`

Run the full Intent → Impact → Risk pipeline on a request.

```bash
knowlyx analyze "add rate limiting to /login" --repo .
knowlyx analyze "..." --repo . --json
```

### `impact`

Show the blast radius of a planned change (single repo).

```bash
knowlyx impact "rename users.email column" --repo .
```

### `conventions`

List all detected conventions + forbidden patterns.

```bash
knowlyx conventions .
```

### `assets`

List reusable assets (components, hooks, utils, services), optionally filtered by domain.

```bash
knowlyx assets             # all assets
knowlyx assets billing     # filter by domain
```

### `pack`

Show the built-in cognition pack for a domain.

```bash
knowlyx pack auth
knowlyx pack payment
```

Available domains: `auth`, `otp`, `payment`, `webhook`, `order`, `notification`, `worker`.

### `graph`

Export the cognitive graph for a single repo.

```bash
knowlyx graph mermaid --repo .
knowlyx graph dot --repo . | dot -Tpng > graph.png
knowlyx graph react_flow --repo .
```

## Memory commands

### `memory list`

List all memory entries (approved + pending), optionally filtered.

```bash
knowlyx memory list --repo .
knowlyx memory list --domain billing --repo .
```

### `memory recall`

Fuzzy search approved memory.

```bash
knowlyx memory recall "rate limit" --repo .
```

### `memory decide`

Record an auto-approved team decision.

```bash
knowlyx memory decide billing \
  "Use Stripe for subscriptions" \
  --body "Stripe Billing for B2C, manual invoice for B2B over $10k"
```

### `memory forget`

Delete a memory entry.

```bash
knowlyx memory forget <entry-id>
```

## Workspace (multi-repo)

### `workspace create`

Create a central workspace at `~/.knowlyx/workspaces/<name>/`.

```bash
knowlyx workspace create my-product
```

### `workspace list`

List all central workspaces.

```bash
knowlyx workspace list
```

### `workspace init`

Create a `knowlyx.toml` in the current folder (legacy sibling-layout mode).

```bash
knowlyx workspace init
```

### `workspace scan`

Scan all repos in the current workspace and show summary.

```bash
knowlyx workspace scan
```

### `workspace impact`

Cross-repo blast radius for a change in one repo.

```bash
knowlyx workspace impact api --change "rename users.email"
```

### `workspace graph`

Export the cross-repo graph.

```bash
knowlyx workspace graph mermaid
knowlyx workspace graph react_flow --json
```

## Link (per-repo)

### `link`

Connect this repo to a central workspace.

```bash
knowlyx link my-product \
  --role backend \
  --domains billing,auth \
  --critical
```

This writes `.knowlyx/config.toml` — commit it to git so every clone connects automatically.

### `unlink`

Remove the link.

```bash
knowlyx unlink
```

### `migrate`

Move legacy `<repo>/.knowlyx/{memory,approvals}.json` into the central workspace.

```bash
knowlyx migrate
knowlyx migrate --workspace my-product --dry-run
```

## Approval queue

### `approval list`

List pending approval requests.

```bash
knowlyx approval list
```

### `approval show`

Show details of one request.

```bash
knowlyx approval show <id>
```

### `approval approve` / `reject`

```bash
knowlyx approval approve <id>
knowlyx approval reject <id> --reason "too risky before release"
```

## MCP server

### `mcp`

Start the MCP server (stdio by default — for Claude Code, Cursor, Cline).

```bash
knowlyx mcp --repo .
knowlyx mcp --sse --port 8765 --repo .
```

## Global flags

| Flag | Description |
|---|---|
| `--repo / -r` | Path to the repo (default `.`) |
| `--workspace / -w` | Path to workspace root |
| `--json` | Output raw JSON instead of pretty table |
| `--help` | Show help for any command |

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `KNOWLYX_HOME` | `~/.knowlyx` | Central knowledge home |
| `QDRANT_URL` | (none) | Enable semantic search via Qdrant |
| `QDRANT_API_KEY` | (none) | Qdrant cloud auth |
