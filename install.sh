#!/bin/sh
# Sage installer — one command, any repo. Sets up (or updates) Sage:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh)"
#
# Lets you pick which AI tools to wire up with a checkbox picker:
#   move   : Up/Down arrows, or j / k, or Tab
#   toggle : Space (current row) or press 1-7 (that row, instantly)
#   a      : select/clear all      Enter : confirm
# Arrow keys are swallowed by some Windows consoles (git-bash/MSYS) — the
# letter/number keys always work, so the picker stays fully usable everywhere.
# It NEVER touches your own knowledge under agents/sage/<domain>/.
#
# Non-interactive? Prefix with SAGE_TOOLS:
#   SAGE_TOOLS='claude,cursor' bash -c "$(curl -fsSL .../install.sh)"   (or 'all')
set -eu

REPO="https://github.com/qorstack/sage"
ALL="claude cursor windsurf cline copilot codex gemini"
NTOOLS=7
TTY_STTY=""
TMP=""

cleanup() {
  [ -n "$TTY_STTY" ] && stty "$TTY_STTY" </dev/tty 2>/dev/null || true
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

toggle_row() { # $1 = row number
  tk=$(num_to_key "$1")
  eval "tv=\$chk_$tk"
  if [ "$tv" = 1 ]; then eval "chk_$tk=0"; else eval "chk_$tk=1"; fi
}

# Checkbox picker over /dev/tty using stty raw reads (dd) — the input path that
# works on git-bash/MSYS as well as macOS/Linux. Movement never depends on
# arrows alone: j/k, Tab, and instant 1-7 toggles always work.
# Returns 1 when unusable so the caller falls back to the numbered prompt.
select_tools_tui() {
  [ -r /dev/tty ] && [ -w /dev/tty ] || return 1
  command -v stty >/dev/null 2>&1 || return 1
  command -v dd >/dev/null 2>&1 || return 1
  TTY_STTY=$(stty -g </dev/tty 2>/dev/null) || return 1
  stty -echo -icanon min 1 time 0 </dev/tty 2>/dev/null || { TTY_STTY=""; return 1; }
  printf '\033[?25l' >/dev/tty

  ESC=$(printf '\033'); CR=$(printf '\r'); TAB=$(printf '\t')
  pos=1
  for k in $ALL; do eval "chk_$k=0"; done

  printf '\nSage: select AI tools\n  1-7 toggle a row - Space toggle - j/k or arrows move - a all - Enter confirm\n\n' >/dev/tty
  drawn=0
  while :; do
    [ "$drawn" = 1 ] && printf '\033[%dA' "$NTOOLS" >/dev/tty
    drawn=1
    i=1
    for k in $ALL; do
      eval "v=\$chk_$k"
      box='[ ]'; [ "$v" = 1 ] && box='[x]'
      if [ "$i" -eq "$pos" ]; then
        printf '\r\033[K\033[36m> %s %d) %s\033[0m\n' "$box" "$i" "$(key_name "$k")" >/dev/tty
      else
        printf '\r\033[K  %s %d) %s\n' "$box" "$i" "$(key_name "$k")" >/dev/tty
      fi
      i=$((i + 1))
    done
    c=$(dd bs=1 count=1 2>/dev/null </dev/tty) || c=""
    case "$c" in
      "" | "$CR") break ;; # Enter (NL is stripped by $(...), CR arrives raw)
      " ") toggle_row "$pos" ;;
      [1-7]) pos=$c; toggle_row "$c" ;;
      k | K | w | W) pos=$((pos > 1 ? pos - 1 : NTOOLS)) ;;
      j | J | s | S | "$TAB") pos=$((pos < NTOOLS ? pos + 1 : 1)) ;;
      a | A)
        on=1; for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 0 ] && on=0; done
        nv=1; [ "$on" = 1 ] && nv=0
        for k in $ALL; do eval "chk_$k=$nv"; done ;;
      "$ESC")
        # arrow keys: read the rest of the sequence without blocking
        stty -icanon min 0 time 2 </dev/tty 2>/dev/null || true
        seq=$(dd bs=1 count=2 2>/dev/null </dev/tty) || seq=""
        stty -icanon min 1 time 0 </dev/tty 2>/dev/null || true
        case "$seq" in
          "[A" | "OA" | "[Z") pos=$((pos > 1 ? pos - 1 : NTOOLS)) ;;
          "[B" | "OB") pos=$((pos < NTOOLS ? pos + 1 : 1)) ;;
        esac ;;
    esac
  done

  stty "$TTY_STTY" </dev/tty 2>/dev/null || true
  TTY_STTY=""
  printf '\033[?25h\n' >/dev/tty
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

# --- choose tools: SAGE_TOOLS override, else checkbox picker, else prompt, else all ---
if [ -n "${SAGE_TOOLS:-}" ]; then
  parse_tools "$SAGE_TOOLS"
elif select_tools_tui; then
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
