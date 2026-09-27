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
| `sage-flow.md`            | Build + verify design → `agents/sage/flows/<slug>/flow.md`          | checklist toggle `plan-flow`       |
| `sage-ticket.md`          | Cut clear requirements into implementation tickets, then build them | on demand, after Grill/Flow        |
| `sage-review.md`          | Review a change for correctness + requirement conformance          | on demand, after implementation    |
| `sage-unit-test.md`       | Write unit tests that match the repo's stack                       | explicit specialist command        |
| `sage-e2e-test.md`        | Autonomously explore, encode, run, and validate real E2E behavior | explicit specialist command        |
| `sage-security-review.md` | Review a change for real, exploitable security holes               | explicit specialist command        |
| `sage-docs.md`            | Create/update a plain-Markdown flow doc → `docs/`                  | core `update-docs`                 |
| `sage-learning.md`        | Learn this repo's patterns + research best practices for its stack | on demand                          |
| `sage-refactoring-code.md` | Write/refactor readable code and schemas without speculative layers | on demand                         |
| `sage-update.md`          | Re-run the installer to update Sage to the latest version          | on demand                          |
| `sage-setting.md`         | View/change how `/sage` runs (mode + default steps, per machine)   | on demand                          |

The route guard + run contract (`agents/sage/AGENTS.md` §0) are the dispatcher when `/sage` is invoked:
routes fog to Grill or Wayfinder independently of checklist selection. `AGENTS.md`
§0 also classifies **posture** (`preserve`/`extend`/`refactor`/`redesign`/
`greenfield`) — a second axis, not a new command — that re-weights the reuse
scan (§1.3) and, for `redesign`/`greenfield`, adds a Direction section to
`/sage-flow`'s output. Specialist commands run only when the human explicitly
invokes or requests them.
`automate-test` (run the existing suite and report the real output) is a core
step of `/sage` itself, not a separate command and never permission to author tests.

Two boundaries that must not blur:

- **Tickets.** `/sage-wayfinder` owns _decision_ tickets, which remove fog and
  live under `agents/sage/wayfinders/`. `/sage-ticket` owns _implementation_
  tickets, which deliver the destination and live in
  `agents/sage/flows/<slug>/tickets.md`. One backend each; never mirrored.
- **Review.** `/sage-review` owns correctness and requirement conformance.
  `/sage-security-review` owns exploitable holes and
  `/sage-refactoring-code` owns readability. Each hands findings to the other
  rather than half-covering its neighbour's job.

Risk policy has one source of truth: `agents/sage/AGENTS.md` §1.4 and §4. Commands may add
domain-specific evidence, but may not loosen its HIGH-risk gate or replace
driver-specific controls with a generic risk label.
