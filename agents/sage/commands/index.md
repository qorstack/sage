# Sage commands (canonical, single source of truth)

Every Sage command's full body lives here, once. The per-tool files under
`integrations/` (`.claude`, `.cursor`, `.windsurf`, `.clinerules`, `.github`,
`.codex`, `gemini.md`) are **thin pointers** to these files — edit the command
here and every tool follows. This is the "keep integrations thin" rule in
practice.

| Command                   | What it does                                                       | Invoked by                         |
| ------------------------- | ------------------------------------------------------------------ | ---------------------------------- |
| `sage.md`                 | The cognition pipeline — role, knowledge, risk controls, evidence  | automatically, before any change   |
| `sage-grill.md`           | Resolve single-session fog + glossary/checkpoint → clear spec      | route `foggy-single-session`       |
| `sage-wayfinder.md`       | Map and resolve multi-session fog as durable decision tickets      | route `large-multi-session`        |
| `sage-flow.md`            | Build + verify an implementation-ready flow → `agents/sage/flows/` | checklist toggle `plan-flow`       |
| `sage-unit-test.md`       | Write unit tests that match the repo's stack                       | checklist toggle `unit-test`       |
| `sage-e2e-test.md`        | Drive the app end-to-end (Playwright/k6/…) and prove the flow      | checklist toggle `e2e-test`        |
| `sage-security-review.md` | Review a change for real, exploitable security holes               | checklist toggle `security-review` |
| `sage-docs.md`            | Create/update a plain-Markdown flow doc → `docs/`                  | core `update-docs`                 |
| `sage-learning.md`        | Learn this repo's patterns + research best practices for its stack | on demand                          |
| `sage-update.md`          | Re-run the installer to update Sage to the latest version          | on demand                          |
| `sage-setting.md`         | View/change how `/sage` runs (mode + default steps, per machine)   | on demand                          |

The route guard + run checklist (`AGENTS.md` §0) are the dispatcher: `/sage`
routes fog to Grill or Wayfinder independently of checklist selection, then runs
the applicable confirmed specialist commands after requirements are clear.
`automate-test` (run the existing suite and report the real output) is a core
step of `/sage` itself, not a separate command.

Risk policy has one source of truth: `AGENTS.md` §1.4 and §4. Commands may add
domain-specific evidence, but may not loosen its HIGH-risk gate or replace
driver-specific controls with a generic risk label.
