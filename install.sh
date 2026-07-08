#!/bin/sh
# Sage installer — one command, any repo. Sets up (or updates) Sage:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh)"
#
# Lets you pick which AI tools to wire up with a checkbox picker:
#   press 1-7 to toggle a row (instant, no Enter needed)
#   a = select/clear all         Enter = confirm
# Number keys are plain characters, so this works in every console — including
# git-bash/MSYS, which swallows arrow keys.
# It NEVER touches your own knowledge under agents/sage/<domain>/.
#
# Non-interactive? Prefix with SAGE_TOOLS:
#   SAGE_TOOLS='claude,cursor' bash -c "$(curl -fsSL .../install.sh)"   (or 'all')
set -eu

REPO="https://github.com/qorstack/sage"
ALL="claude codex cursor copilot gemini windsurf cline"
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
    1) echo claude ;; 2) echo codex ;; 3) echo cursor ;; 4) echo copilot ;;
    5) echo gemini ;; 6) echo windsurf ;; 7) echo cline ;; *) echo "" ;;
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
# works on git-bash/MSYS as well as macOS/Linux. Number keys toggle instantly;
# no cursor, no arrows — nothing a console can swallow.
# Returns 1 when unusable so the caller falls back to the numbered prompt.
select_tools_tui() {
  [ -r /dev/tty ] && [ -w /dev/tty ] || return 1
  command -v stty >/dev/null 2>&1 || return 1
  command -v dd >/dev/null 2>&1 || return 1
  TTY_STTY=$(stty -g </dev/tty 2>/dev/null) || return 1
  stty -echo -icanon min 1 time 0 </dev/tty 2>/dev/null || { TTY_STTY=""; return 1; }
  printf '\033[?25l' >/dev/tty

  CR=$(printf '\r')
  for k in $ALL; do eval "chk_$k=0"; done

  printf '\nSage: select AI tools — press 1-7 to toggle, a = all, Enter = confirm\n\n' >/dev/tty
  drawn=0
  while :; do
    [ "$drawn" = 1 ] && printf '\033[%dA' "$NTOOLS" >/dev/tty
    drawn=1
    i=1
    for k in $ALL; do
      eval "v=\$chk_$k"
      if [ "$v" = 1 ]; then
        printf '\r\033[K  \033[36m[x] %d) %s\033[0m\n' "$i" "$(key_name "$k")" >/dev/tty
      else
        printf '\r\033[K  [ ] %d) %s\n' "$i" "$(key_name "$k")" >/dev/tty
      fi
      i=$((i + 1))
    done
    c=$(dd bs=1 count=1 2>/dev/null </dev/tty) || c=""
    case "$c" in
      "" | "$CR") break ;; # Enter (NL is stripped by $(...), CR arrives raw)
      [1-7]) toggle_row "$c" ;;
      a | A)
        on=1; for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 0 ] && on=0; done
        nv=1; [ "$on" = 1 ] && nv=0
        for k in $ALL; do eval "chk_$k=$nv"; done ;;
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
printf 'Sage: fetching latest from qorstack/sage ...\n'
if ! git clone --depth 1 --quiet "$REPO" "$TMP" >/dev/null 2>&1; then
  echo "Sage: git clone failed. Check your network and try again."
  exit 1
fi
printf '  \342\234\223 fetched\n'

# --- protocol + Sage-owned files. Clears only what Sage owns; your knowledge
#     (agents/sage/<domain>/, roles/, flows/, index.md), generated docs, and
#     .sage-local.json are never touched. ---
printf 'Sage: writing protocol + commands ...\n'
cp "$TMP/AGENTS.md" ./AGENTS.md
printf '  \342\234\223 AGENTS.md\n'
rm -rf agents/sage/commands                       # 100% Sage-owned; clears any old/renamed command
mkdir -p agents/sage
cp -r "$TMP/agents/sage/commands" agents/sage/commands
printf '  \342\234\223 agents/sage/commands/ (%s commands)\n' "$(ls "$TMP/agents/sage/commands"/*.md 2>/dev/null | grep -c . )"
cp "$TMP/agents/sage/docs-style-template.md" agents/sage/docs-style-template.md
printf '  \342\234\223 agents/sage/docs-style-template.md\n'
# migrate old layout: the style-guide used to sit in agents/sage/docs/ next to
# generated docs — remove only the old Sage assets there, never the folder itself.
rm -f agents/sage/docs/docs-style-template.md agents/sage/docs/sage-docs.css agents/sage/docs/sage-docs.js

# --- starter knowledge (seed only if absent: never clobber the team's edits) ---
[ -f agents/sage/index.md ] || cp "$TMP/agents/sage/index.md" agents/sage/index.md
[ -d agents/sage/roles ] || cp -r "$TMP/agents/sage/roles" agents/sage/roles

# --- install the selected tools' thin adapters ---
printf 'Sage: wiring up adapters ...\n'
installed=""
for k in $picked; do
  if [ "$k" = gemini ]; then
    cp "$TMP/integrations/gemini.md" ./GEMINI.md
  else
    src=$(key_src "$k")
    mkdir -p "$src"
    find "$src" -name 'sage*' -type f -delete 2>/dev/null || true # drop renamed/removed adapters
    cp -r "$TMP/integrations/$src/." "$src/"
  fi
  printf '  \342\234\223 %s\n' "$(key_name "$k")"
  installed="$installed $(key_name "$k"),"
done

cat <<EOF

Sage installed. Adapters for:${installed%,}

Commands now available:
  /sage                 run before any code change (plan, test, review, capture)
  /sage-flow            design + verify an implementation-ready flow before coding
  /sage-unit-test       write unit tests that match this repo's stack
  /sage-e2e-test        drive the app end-to-end (Playwright/Cypress/k6/…) and prove the flow
  /sage-security-review review a change for real, exploitable security holes
  /sage-docs            turn a spec/flow into a plain-Markdown doc in docs/
  /sage-learning        learn this repo's patterns + research best practices for its stack
  /sage-setting         change how /sage runs (mode: auto/ask, default steps)
  /sage-update          re-run this installer to update Sage

Next: run  /sage-learning  to seed knowledge from your codebase.
EOF
