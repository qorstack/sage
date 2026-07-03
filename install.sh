#!/bin/sh
# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh | sh
#
# It fetches the protocol + commands, detects which AI tools this repo uses, and
# drops the matching thin adapters. It NEVER touches your own knowledge under
# agents/sage/<domain>/ — only Sage's own system files are overwritten.
set -eu

REPO="https://github.com/qorstack/sage"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Sage · fetching…"
git clone --depth 1 "$REPO" "$TMP" >/dev/null 2>&1

# --- protocol + shared system files (always overwrite: these are Sage itself) ---
cp "$TMP/AGENTS.md" ./AGENTS.md
mkdir -p agents/sage/commands agents/sage/docs
cp "$TMP/agents/sage/commands/"*.md agents/sage/commands/
cp "$TMP/agents/sage/docs/docs-style-template.md" agents/sage/docs/

# --- starter knowledge (seed only if absent: never clobber the team's edits) ---
[ -f agents/sage/index.md ] || cp "$TMP/agents/sage/index.md" agents/sage/index.md
[ -d agents/sage/roles ] || cp -r "$TMP/agents/sage/roles" agents/sage/roles

# --- detect tools present in this repo, install each one's thin adapters ---
found=""
for t in .claude .cursor .windsurf .clinerules .github .codex; do
  if [ -d "$t" ]; then
    mkdir -p "$t"
    cp -r "$TMP/integrations/$t/." "$t/"
    found="$found $t"
  fi
done
if [ -f GEMINI.md ] || [ -f .gemini/GEMINI.md ]; then
  cp "$TMP/integrations/gemini.md" ./GEMINI.md
  found="$found GEMINI.md"
fi

# --- none found → default to Claude Code ---
if [ -z "$found" ]; then
  mkdir -p .claude
  cp -r "$TMP/integrations/.claude/." ".claude/"
  found=" .claude (default)"
fi

echo "Sage · installed. AGENTS.md + agents/sage/ + adapters for:$found"
echo "Next: run  /sage-learning  to seed knowledge from your codebase."
