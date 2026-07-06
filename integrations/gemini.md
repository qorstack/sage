# Sage

This project uses **Sage**, a cognition protocol. Before writing or modifying any
code, read and follow **`AGENTS.md`** at the repo root — it is the single source
of truth (role selection, the run checklist in §0, risk header, knowledge
capture, the mandatory summary block). Follow it verbatim.

## Commands

Sage's commands live, in full, under **`agents/sage/commands/`**. This file is a
thin adapter — to run any command, open its canonical file and follow it verbatim.
Don't rely on a copy here; the canonical file is authoritative.

| Command                | Run this file                                  | When                                     |
| ---------------------- | ---------------------------------------------- | ---------------------------------------- |
| `sage`                 | `agents/sage/commands/sage.md`                 | before any non-trivial code change       |
| `sage-flow`            | `agents/sage/commands/sage-flow.md`            | design a feature/journey before coding   |
| `sage-unit-test`       | `agents/sage/commands/sage-unit-test.md`       | write unit tests for a target            |
| `sage-e2e-test`        | `agents/sage/commands/sage-e2e-test.md`        | drive the app end-to-end and prove it    |
| `sage-security-review` | `agents/sage/commands/sage-security-review.md` | review a change for security holes       |
| `sage-docs`            | `agents/sage/commands/sage-docs.md`            | turn a document into a Markdown flow doc |
| `sage-learning`        | `agents/sage/commands/sage-learning.md`        | learn this codebase's patterns           |
| `sage-search-skill`    | `agents/sage/commands/sage-search-skill.md`    | research best practices for the stack    |
| `sage-update`          | `agents/sage/commands/sage-update.md`          | update Sage to the latest version        |

The run checklist in `AGENTS.md` §0 is the dispatcher: `/sage` decides which
commands apply, asks you to confirm, then runs the confirmed ones.
