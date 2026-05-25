# CLI reference

Every Knowai command. Run `knowai --help` for live help.

## Project commands

### `scan`

Scan a repo and show its cognitive profile.

```bash
knowai scan [path]
knowai scan . --json
```

### `analyze`

Run the full Intent → Impact → Risk pipeline on a request.

```bash
knowai analyze "add rate limiting to /login" --repo .
knowai analyze "..." --repo . --json
```

### `impact`

Show the blast radius of a planned change (single repo).

```bash
knowai impact "rename users.email column" --repo .
```

### `conventions`

List all detected conventions + forbidden patterns.

```bash
knowai conventions .
```

### `assets`

List reusable assets (components, hooks, utils, services), optionally filtered by domain.

```bash
knowai assets             # all assets
knowai assets billing     # filter by domain
```

### `pack`

Show the built-in cognition pack for a domain.

```bash
knowai pack auth
knowai pack payment
```

Available domains: `auth`, `otp`, `payment`, `webhook`, `order`, `notification`, `worker`.

### `graph`

Export the cognitive graph for a single repo.

```bash
knowai graph mermaid --repo .
knowai graph dot --repo . | dot -Tpng > graph.png
knowai graph react_flow --repo .
```

## Memory commands

### `memory list`

List all memory entries (approved + pending), optionally filtered.

```bash
knowai memory list --repo .
knowai memory list --domain billing --repo .
```

### `memory recall`

Fuzzy search approved memory.

```bash
knowai memory recall "rate limit" --repo .
```

### `memory decide`

Record an auto-approved team decision.

```bash
knowai memory decide billing \
  "Use Stripe for subscriptions" \
  --body "Stripe Billing for B2C, manual invoice for B2B over $10k"
```

### `memory forget`

Delete a memory entry.

```bash
knowai memory forget <entry-id>
```

## Workspace (multi-repo)

### `workspace create`

Create a central workspace at `~/.knowai/workspaces/<name>/`.

```bash
knowai workspace create my-product
```

### `workspace list`

List all central workspaces.

```bash
knowai workspace list
```

### `workspace init`

Create a `knowai.toml` in the current folder (legacy sibling-layout mode).

```bash
knowai workspace init
```

### `workspace scan`

Scan all repos in the current workspace and show summary.

```bash
knowai workspace scan
```

### `workspace impact`

Cross-repo blast radius for a change in one repo.

```bash
knowai workspace impact api --change "rename users.email"
```

### `workspace graph`

Export the cross-repo graph.

```bash
knowai workspace graph mermaid
knowai workspace graph react_flow --json
```

## Link (per-repo)

### `link`

Connect this repo to a central workspace.

```bash
knowai link my-product \
  --role backend \
  --domains billing,auth \
  --critical
```

This writes `.knowai/config.toml` — commit it to git so every clone connects automatically.

### `unlink`

Remove the link.

```bash
knowai unlink
```

### `migrate`

Move legacy `<repo>/.knowai/{memory,approvals}.json` into the central workspace.

```bash
knowai migrate
knowai migrate --workspace my-product --dry-run
```

## Approval queue

### `approval list`

List pending approval requests.

```bash
knowai approval list
```

### `approval show`

Show details of one request.

```bash
knowai approval show <id>
```

### `approval approve` / `reject`

```bash
knowai approval approve <id>
knowai approval reject <id> --reason "too risky before release"
```

## MCP server

### `mcp`

Start the MCP server (stdio by default — for Claude Code, Cursor, Cline).

```bash
knowai mcp --repo .
knowai mcp --sse --port 8765 --repo .
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
| `KNOWLYX_HOME` | `~/.knowai` | Central knowledge home |
| `QDRANT_URL` | (none) | Enable semantic search via Qdrant |
| `QDRANT_API_KEY` | (none) | Qdrant cloud auth |
