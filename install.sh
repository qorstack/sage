#!/usr/bin/env bash
# Knowlyx one-line installer (macOS / Linux)
#   curl -fsSL https://raw.githubusercontent.com/qorstack/knowai/main/install.sh | bash
#
# Or with workspace name + Claude Code registration:
#   curl -fsSL https://raw.githubusercontent.com/qorstack/knowai/main/install.sh | bash -s -- --workspace my-product --claude

set -euo pipefail

WORKSPACE=""
LINK_CLAUDE=false
REPO_PATH="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --claude) LINK_CLAUDE=true; shift ;;
    --repo) REPO_PATH="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: install.sh [--workspace NAME] [--claude] [--repo PATH]"
      exit 0 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

echo "→ Knowlyx installer"

# 1. Ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
  echo "→ Installing uv (https://astral.sh/uv)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Install knowlyx as a tool
echo "→ Installing knowlyx"
uv tool install git+https://github.com/qorstack/knowai.git --upgrade

# 3. Smoke test
knowlyx --version

# 4. Optional workspace setup
if [[ -n "$WORKSPACE" ]]; then
  if ! knowlyx workspace list 2>/dev/null | grep -q "$WORKSPACE"; then
    echo "→ Creating workspace '$WORKSPACE'"
    knowlyx workspace create "$WORKSPACE"
  fi
  echo "→ Linking $REPO_PATH to workspace '$WORKSPACE'"
  (cd "$REPO_PATH" && knowlyx init --link "$WORKSPACE")
fi

# 5. Optional Claude Code registration
if [[ "$LINK_CLAUDE" == "true" ]]; then
  if command -v claude >/dev/null 2>&1; then
    echo "→ Registering MCP server with Claude Code"
    (cd "$REPO_PATH" && claude mcp add knowlyx -- uvx knowlyx mcp --repo .)
  else
    echo "⚠ claude CLI not found. Skipping Claude Code registration."
    echo "   Install Claude Code from https://docs.anthropic.com/claude-code, then run:"
    echo "   claude mcp add knowlyx -- uvx knowlyx mcp --repo ."
  fi
fi

echo ""
echo "✓ Done. Try:"
echo "   knowlyx scan ."
echo "   knowlyx analyze 'add password reset' --repo ."
