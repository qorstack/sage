#!/bin/sh
# Sage installer — one command, any repo. Sets up (or updates) Sage:
#   sh -c "$(curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh)"
#
# (Use the sh -c "$(...)" form — NOT `curl | sh` — so the picker can read your
# keyboard. With `curl | sh` the script's stdin is the pipe, not the terminal.)
#
# Lets you pick which AI tools to wire up, fetches the protocol + commands, and
# drops the adapters you pick. It NEVER touches your own knowledge under
# agents/sage/<domain>/.
#
# Non-interactive? Prefix with SAGE_TOOLS, e.g.
#   SAGE_TOOLS='claude,cursor' sh -c "$(curl -fsSL .../install.sh)"   (or 'all')
set -eu

REPO="https://github.com/qorstack/sage"
ALL="claude cursor windsurf cline copilot codex gemini"
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

read_choice() {  # read one interactive line into $line; return 1 if no input
  if [ -t 0 ]; then
    IFS= read -r line          # stdin is the terminal (sh -c "$(curl ...)")
  elif [ -r /dev/tty ]; then
    IFS= read -r line </dev/tty # fallback for `curl | sh`
  else
    return 1
  fi
}

parse_tools() {  # $1 = raw string -> sets $picked
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

# Arrow-key + space checkbox over /dev/tty. Sets $picked. Returns 1 if unusable.
select_tools_tui() {
  # Raw-mode arrow keys are unreliable under Windows shells (git-bash / MSYS /
  # Cygwin) — the console is not a real PTY. Bail so the caller uses the
  # number-toggle menu instead. (On Windows, prefer the PowerShell installer.)
  case "$(uname -s 2>/dev/null || echo x)" in
    MINGW* | MSYS* | CYGWIN* | Windows_NT) return 1 ;;
  esac
  [ -r /dev/tty ] || return 1
  command -v stty >/dev/null 2>&1 || return 1
  command -v dd >/dev/null 2>&1 || return 1
  TTY_STTY=$(stty -g </dev/tty 2>/dev/null) || return 1
  stty -echo -icanon min 1 time 0 </dev/tty 2>/dev/null || { TTY_STTY=""; return 1; }
  printf '\033[?25l' >/dev/tty 2>/dev/null || true

  ESC=$(printf '\033'); CR=$(printf '\r')
  pos=1; rows=7; drawn=0
  for k in $ALL; do eval "chk_$k=0"; done
  printf '\nSage: select AI tools\n' >/dev/tty
  printf '  Up/Down move  -  Space toggle  -  a all  -  Enter confirm\n\n' >/dev/tty

  while :; do
    [ "$drawn" -eq 1 ] && printf '\033[%dA' "$rows" >/dev/tty
    drawn=1
    i=1
    for k in $ALL; do
      eval "v=\$chk_$k"; box='[ ]'; [ "$v" = 1 ] && box='[x]'
      if [ "$i" -eq "$pos" ]; then
        printf '\r\033[K\033[36m> %s %s\033[0m\n' "$box" "$(key_name "$k")" >/dev/tty
      else
        printf '\r\033[K  %s %s\n' "$box" "$(key_name "$k")" >/dev/tty
      fi
      i=$((i + 1))
    done

    c=$(dd bs=1 count=1 2>/dev/null </dev/tty) || c=""
    case "$c" in
      "" | "$CR") break ;;  # Enter (NL stripped to empty, or raw CR)
      " ")
        cur=$(num_to_key "$pos"); eval "v=\$chk_$cur"
        if [ "$v" = 1 ]; then eval "chk_$cur=0"; else eval "chk_$cur=1"; fi ;;
      a | A)
        on=1; for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 0 ] && on=0; done
        nv=1; [ "$on" = 1 ] && nv=0
        for k in $ALL; do eval "chk_$k=$nv"; done ;;
      "$ESC")
        seq=$(dd bs=1 count=2 2>/dev/null </dev/tty) || seq=""
        case "$seq" in
          "[A" | "OA") [ "$pos" -gt 1 ] && pos=$((pos - 1)) || pos=$rows ;;
          "[B" | "OB") [ "$pos" -lt "$rows" ] && pos=$((pos + 1)) || pos=1 ;;
        esac ;;
    esac
  done

  stty "$TTY_STTY" </dev/tty 2>/dev/null || true
  TTY_STTY=""
  printf '\033[?25h\n' >/dev/tty
  picked=""
  for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 1 ] && picked="$picked $k"; done
  return 0
}

# [x] checkbox by number-toggle over /dev/tty (uses line-read; works everywhere,
# including git-bash). Sets $picked. Returns 1 if there is no tty.
select_tools_menu() {
  { [ -t 0 ] || [ -r /dev/tty ]; } || return 1
  for k in $ALL; do eval "chk_$k=0"; done
  printf '\nSage: select AI tools — type a number to toggle, "a" for all, Enter when done.\n' >/dev/tty
  drawn=0
  while :; do
    # redraw the list + prompt in place so only the latest state shows
    [ "$drawn" = 1 ] && printf '\033[8A\033[J' >/dev/tty
    drawn=1
    i=1
    for k in $ALL; do
      eval "v=\$chk_$k"
      if [ "$v" = 1 ]; then
        printf '  \033[36m[x] %d) %s\033[0m\n' "$i" "$(key_name "$k")" >/dev/tty
      else
        printf '  [ ] %d) %s\n' "$i" "$(key_name "$k")" >/dev/tty
      fi
      i=$((i + 1))
    done
    printf 'toggle (number) / a=all / Enter=confirm: ' >/dev/tty
    read_choice || line=""
    [ -z "$line" ] && break
    case "$(printf '%s' "$line" | tr 'A-Z' 'a-z' | tr -d ' ')" in
      a | all) for k in $ALL; do eval "chk_$k=1"; done ;;
      *)
        for tok in $(printf '%s' "$line" | tr ',' ' '); do
          case "$tok" in
            [1-7])
              ck=$(num_to_key "$tok"); eval "v=\$chk_$ck"
              if [ "$v" = 1 ]; then eval "chk_$ck=0"; else eval "chk_$ck=1"; fi ;;
          esac
        done ;;
    esac
  done
  picked=""
  for k in $ALL; do eval "v=\$chk_$k"; [ "$v" = 1 ] && picked="$picked $k"; done
  return 0
}

# --- choose tools: SAGE_TOOLS override, else arrow TUI (unix), else menu, else all ---
if [ -n "${SAGE_TOOLS:-}" ]; then
  parse_tools "$SAGE_TOOLS"
elif select_tools_tui; then
  :
elif select_tools_menu; then
  :
else
  picked="$ALL"
fi

if [ -z "$(printf '%s' "$picked" | tr -d ' ')" ]; then
  echo "Sage: no tools selected. Nothing to do."
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
