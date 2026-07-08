# /sage-setting — view and change how /sage runs (per machine)

Read and update `/sage`'s per-machine preferences in `.sage-local.json` so the
user never hand-edits JSON. This is a small, mechanical command — no §0 checklist,
no plan, no code analysis. Just show or change settings, then confirm.

`.sage-local.json` is **gitignored and per-machine** — it is never shared with the
team or committed.

---

## Config shape (`.sage-local.json`, at the repo root)

```json
{
  "version": 2,
  "mode": "auto",
  "checklist": {
    "auto-switch-model": true,
    "plan-flow": true,
    "unit-test": true,
    "e2e-test": false,
    "security-review": false
  }
}
```

- **`mode`** — `"auto"` (decide the steps and proceed without prompting) or
  `"ask"` (show the checklist and wait for the human, every code change).
- **`checklist`** — the default checked/unchecked state for the five steps; the
  recommendation engine still adjusts per task.

**Migration:** if the file has the old `askMode` field, convert it first —
`askMode: "smart"` → `mode: "auto"`, `askMode: "always"` → `mode: "ask"` — set
`version: 2`, drop `askMode`, and **preserve any unknown fields**.

---

## What to do

**1. Read** `.sage-local.json` at the active repo root (migrate old `askMode` if
present; create it with the defaults above if missing; add `.sage-local.json` to
`.gitignore` if not already ignored).

**2. Act on the request:**

| The user says…                         | Do this                                                                                                                             |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| "show settings" / just `/sage-setting` | Print the active repo, `mode`, the checklist defaults, and whether `.sage-local.json` is gitignored. Then offer the changes below.  |
| "ask me every time" / "mode ask"       | Set `mode: "ask"`.                                                                                                                  |
| "don't ask / auto" / "mode auto"       | Set `mode: "auto"`.                                                                                                                 |
| "default steps 1,3,5" / names          | Set those `checklist` keys `true`, the rest `false` (1=auto-switch-model, 2=plan-flow, 3=unit-test, 4=e2e-test, 5=security-review). |
| "all steps on"                         | Set all five `checklist` keys `true`.                                                                                               |
| "reset"                                | Restore the default config above (keep the file gitignored).                                                                        |

If the request is ambiguous, use **AskUserQuestion** (or a Markdown fallback) to
ask two things: **mode** (Ask every time / Auto — don't prompt) and **default
steps** (multi-select the five). Then apply.

**3. Write** the updated `.sage-local.json` (valid JSON, preserve unknown fields
except on reset) and **echo the result** on one line, e.g.:

```text
Sage settings · mode: ask · default steps: auto-switch-model, plan-flow, unit-test · .sage-local.json (gitignored)
```

Then stop. No summary block, no knowledge capture — this only edits local config.
