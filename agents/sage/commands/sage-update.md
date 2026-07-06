# /sage-update — update Sage in this repo to the latest version

**A fixed, mechanical procedure. Do exactly the steps below and nothing else** —
no §0 checklist, no gauging, no plan, no reading the codebase, no extra reasoning.
The whole point is to spend as few tokens as possible: ask, then run one command.

It re-runs the official installer, which overwrites Sage's own files (`AGENTS.md`,
`agents/sage/commands/`, the style-guide, and the tool adapters) with the latest
from `main`, and **never touches your own knowledge under
`agents/sage/<domain>/`**.

---

## Locked steps

**1. Ask which AI tools to wire up (MANDATORY — always ask, every run).** Call
**AskUserQuestion** with one **multi-select** question,
`"Which AI tools should Sage wire up?"`, listing all seven in this order and
**pre-checking the ones already present in the repo** (a quick check for
`.claude/`, `.codex/`, `.cursor/`, `.github/`, `GEMINI.md`, `.windsurf/`,
`.clinerules/`):

- Claude Code · Codex · Cursor · GitHub Copilot · Gemini · Windsurf · Cline

**2. Map the answer to a comma list** of keys — `claude, codex, cursor, copilot,
gemini, windsurf, cline` — or the literal `all`. Call it `<tools>`.

**3. Run the matching command for this OS — exactly one, nothing else.** Passing
`SAGE_TOOLS` skips the installer's own picker (you already asked), so it runs
non-interactively:

- **Windows (PowerShell tool):**
  ```powershell
  $env:SAGE_TOOLS='<tools>'; irm https://raw.githubusercontent.com/qorstack/sage/main/install.ps1 | iex
  ```
- **macOS / Linux (Bash tool):**
  ```bash
  SAGE_TOOLS='<tools>' bash -c "$(curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/install.sh)"
  ```

**4. Report the installer's one-line result** (which adapters it wrote) and stop.
No summary block, no knowledge capture, no follow-up analysis — this is a
mechanical update, not a code change.

---

**If AskUserQuestion is unavailable** (headless): default `<tools>` to the
adapters already present in the repo, or `all` if none, say which you chose, and
run the command.
