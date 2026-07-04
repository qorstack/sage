#!/bin/sh
# Sage installer — one command, any repo. Sets up (or updates) Sage:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh)"
#
# Lets you pick which AI tools to wire up — an arrow-key checkbox when running
# under bash (git-bash, macOS, Linux), a plain numbered prompt elsewhere —
# fetches the protocol + commands, and drops the adapters you pick. It NEVER
# touches your own knowledge under agents/sage/<domain>/.
#
# Non-interactive? Prefix with SAGE_TOOLS:
#   SAGE_TOOLS='claude,cursor' bash -c "$(curl -fsSL .../install.sh)"   (or 'all')
set -eu

REPO="https://github.com/qorstack/sage"
ALL="claude cursor windsurf cline copilot codex gemini"
NTOOLS=7
TMP=""

cleanup() {
  ( printf '\033[?25h' >/dev/tty ) 2>/dev/null || true
  [ -n "$TMP" ] && rm -rf "$TMP" || true
}
trap cleanup EXIT INT TERM

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

parse_tools() { # $1 = raw string -> sets $picked
  picked=""
  case "$(printf '%s' "$1" | tr 'A-Z' 'a-z' | tr -d ' ')" in
    a | all | "") picked="$ALL"; return ;;
  esac
  for tok in $(printf '%s' "$1" | tr ',' ' '); do
    case "$tok" in
      [1-7]) k=$(num_to_key "$tok") ;;
      claude | cursor | windsurf | cline | copilot | codex | gemini) k="$tok" ;;
      *) k="" ;;
    esac
    [ -n "$k" ] && case " $picked " in *" $k "*) : ;; *) picked="$picked $k" ;; esac
  done
}

collect_picked() {
  picked=""
  for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 1 ] && picked="$picked $k"; done
}

# Arrow-key checkbox — requires bash (git-bash, macOS, and Linux bash all
# qualify; bash's `read -rsn1` handles raw key input itself, no stty games).
# Keys come from fd 3 (the terminal), UI is drawn on stderr.
# Returns 1 when unusable so the caller falls back to the numbered prompt.
select_tools_arrows() {
  [ -n "${BASH_VERSION:-}" ] || return 1
  [ -t 2 ] || return 1
  if [ -t 0 ]; then
    exec 3<&0
  elif [ -r /dev/tty ]; then
    exec 3</dev/tty || return 1
  else
    return 1
  fi

  ESC=$(printf '\033'); CR=$(printf '\r')
  pos=1
  for k in $ALL; do eval "chk_$k=0"; done

  printf '\nSage: select AI tools\n  Up/Down move - Space toggle - a all - Enter confirm\n\n' >&2
  printf '\033[?25l' >&2
  drawn=0
  while :; do
    [ "$drawn" = 1 ] && printf '\033[%dA' "$NTOOLS" >&2
    drawn=1
    i=1
    for k in $ALL; do
      eval "v=\$chk_$k"
      box='[ ]'; [ "$v" = 1 ] && box='[x]'
      if [ "$i" -eq "$pos" ]; then
        printf '\r\033[K\033[36m> %s %s\033[0m\n' "$box" "$(key_name "$k")" >&2
      else
        printf '\r\033[K  %s %s\n' "$box" "$(key_name "$k")" >&2
      fi
      i=$((i + 1))
    done
    key=""
    IFS= read -rsn1 -u3 key 2>/dev/null || { printf '\033[?25h' >&2; return 1; }
    case "$key" in
      "$ESC")
        seq=""
        IFS= read -rsn2 -t 1 -u3 seq 2>/dev/null || seq=""
        case "$seq" in
          "[A" | "OA") pos=$((pos > 1 ? pos - 1 : NTOOLS)) ;;
          "[B" | "OB") pos=$((pos < NTOOLS ? pos + 1 : 1)) ;;
        esac ;;
      " ")
        ck=$(num_to_key "$pos"); eval "v=\$chk_$ck"
        if [ "$v" = 1 ]; then eval "chk_$ck=0"; else eval "chk_$ck=1"; fi ;;
      a | A)
        on=1; for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 0 ] && on=0; done
        nv=1; [ "$on" = 1 ] && nv=0
        for k in $ALL; do eval "chk_$k=$nv"; done ;;
      "" | "$CR") break ;;
    esac
  done
  printf '\033[?25h' >&2
  collect_picked
  return 0
}

# One-shot numbered prompt — plain POSIX, works in any shell with any tty.
select_tools_prompt() {
  if [ -t 0 ]; then
    src=""
  elif [ -r /dev/tty ]; then
    src="/dev/tty"
  else
    return 1
  fi
  {
    printf '\nSage: which AI tools should I wire up?\n'
    i=1
    for k in $ALL; do printf '  %d) %s\n' "$i" "$(key_name "$k")"; i=$((i + 1)); done
    printf 'Enter numbers (e.g. 1,2,5), names, or "a" for all: '
  } >&2
  if [ -n "$src" ]; then
    IFS= read -r line <"$src" || return 1
  else
    IFS= read -r line || return 1
  fi
  parse_tools "$line"
  return 0
}

# --- choose tools: SAGE_TOOLS override, else arrow checkbox, else prompt, else all ---
if [ -n "${SAGE_TOOLS:-}" ]; then
  parse_tools "$SAGE_TOOLS"
elif select_tools_arrows; then
  :
elif select_tools_prompt; then
  :
else
  picked="$ALL"
fi

if [ -z "$(printf '%s' "$picked" | tr -d ' ')" ]; then
  echo "Sage: no tools selected. Nothing to do. (Tip: SAGE_TOOLS='all' to skip the picker.)"
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Sage: git is required but was not found. Install Git, then re-run."
  exit 1
fi

TMP="$(mktemp -d)"
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
