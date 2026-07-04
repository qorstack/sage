#!/bin/sh
# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh | sh
#
# It asks which AI tools to wire up (multi-select), fetches the protocol +
# commands, and drops the matching thin adapters. It NEVER touches your own
# knowledge under agents/sage/<domain>/ — only Sage's own system files.
#
# Non-interactive? Prefix with SAGE_TOOLS, e.g.
#   curl -fsSL .../install.sh | SAGE_TOOLS='claude,cursor' sh   (or 'all')
set -eu

REPO="https://github.com/qorstack/sage"

num_to_key() {
  case "$1" in
    1) echo claude ;; 2) echo cursor ;; 3) echo windsurf ;; 4) echo cline ;;
    5) echo copilot ;; 6) echo codex ;; 7) echo gemini ;; *) echo "" ;;
  esac
}
key_src() {
  case "$1" in
    claude) echo ".claude" ;; cursor) echo ".cursor" ;; windsurf) echo ".windsurf" ;;
    cline) echo ".clinerules" ;; copilot) echo ".github" ;; codex) echo ".codex" ;;
    gemini) echo "gemini" ;; *) echo "" ;;
  esac
}
key_name() {
  case "$1" in
    claude) echo "Claude Code" ;; cursor) echo "Cursor" ;; windsurf) echo "Windsurf" ;;
    cline) echo "Cline" ;; copilot) echo "GitHub Copilot" ;; codex) echo "Codex" ;;
    gemini) echo "Gemini CLI" ;; *) echo "" ;;
  esac
}
ALL="claude cursor windsurf cline copilot codex gemini"

# --- choose tools: SAGE_TOOLS override, else interactive multi-select ---
if [ -n "${SAGE_TOOLS:-}" ]; then
  raw="$SAGE_TOOLS"
elif [ -r /dev/tty ]; then
  printf 'Sage: which AI tools should I wire up?\n'
  printf '  1) Claude Code\n  2) Cursor\n  3) Windsurf\n  4) Cline\n'
  printf '  5) GitHub Copilot\n  6) Codex\n  7) Gemini CLI\n'
  printf 'Enter numbers (e.g. 1,2,5), names, or "a" for all: '
  read raw </dev/tty
else
  raw="all"
fi

case "$(printf '%s' "$raw" | tr 'A-Z' 'a-z' | tr -d ' ')" in
  a|all|"") picked="$ALL" ;;
  *)
    picked=""
    for tok in $(printf '%s' "$raw" | tr ',' ' '); do
      case "$tok" in
        [1-7]) k=$(num_to_key "$tok") ;;
        claude|cursor|windsurf|cline|copilot|codex|gemini) k="$tok" ;;
        *) k="" ;;
      esac
      if [ -n "$k" ]; then
        case " $picked " in *" $k "*) : ;; *) picked="$picked $k" ;; esac
      fi
    done
    ;;
esac
if [ -z "$(printf '%s' "$picked" | tr -d ' ')" ]; then
  echo "Sage: no valid tools selected. Nothing to do."
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Sage: git is required but was not found. Install Git, then re-run."
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
echo "Sage: fetching..."
if ! git clone --depth 1 --quiet "$REPO" "$TMP" >/dev/null 2>&1; then
  echo "Sage: git clone failed. Check your network and try again."
  exit 1
fi

# --- protocol + shared system files (always overwrite: these are Sage itself) ---
cp "$TMP/AGENTS.md" ./AGENTS.md
mkdir -p agents/sage/commands agents/sage/docs
cp "$TMP/agents/sage/commands/"*.md agents/sage/commands/
cp "$TMP/agents/sage/docs/docs-style-template.md" agents/sage/docs/

# --- starter knowledge (seed only if absent: never clobber the team's edits) ---
[ -f agents/sage/index.md ] || cp "$TMP/agents/sage/index.md" agents/sage/index.md
[ -d agents/sage/roles ] || cp -r "$TMP/agents/sage/roles" agents/sage/roles

# --- install the selected tools' thin adapters ---
installed=""
for k in $picked; do
  if [ "$k" = gemini ]; then
    cp "$TMP/integrations/gemini.md" ./GEMINI.md
  else
    src=$(key_src "$k")
    mkdir -p "$src"
    cp -r "$TMP/integrations/$src/." "$src/"
  fi
  installed="$installed $(key_name "$k"),"
done

echo "Sage: installed. AGENTS.md + agents/sage/ + adapters for:${installed%,}"
echo "Next: run  /sage-learning  to seed knowledge from your codebase."
