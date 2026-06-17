<p align="center"><img src="assets/logo-full.png" alt="Sage" width="320"></p>

<h1 align="center">Sage</h1>

<p align="center"><b>Make your AI code like your most senior dev.</b></p>

## The Sage

Every team has a senior who has seen it all — the one who, before touching
anything, quietly asks: *Is this even needed? Will it last? Is it safe? Did we
already agree on this?* That balance of purpose and care has a name in Japan:
**生き甲斐 — ikigai**, your reason for doing.

Sage gives that senior's ikigai to **every AI agent you use**. Before it writes
a line, the agent becomes the right kind of senior for the task, weighs those
four questions against your team's rules, and *then* codes — or stops and asks.

|  | the question | |
| --- | --- | --- |
| 🎯 | **Is it needed?** | …or does something already cover it? |
| ⏳ | **Will it last?** | worth maintaining, in the shape the code already follows? |
| 🛡️ | **Is it safe?** | what's the blast radius — money, auth, data? |
| 🤝 | **Did we agree?** | does it respect the rules in `agents/sage/`? |

No install, no server, no Python. Sage is a cognition protocol in a single
**`AGENTS.md`** — Markdown you read, edit, and `git push`. Any agent that reads
`AGENTS.md` (Claude Code, Cursor, Codex, Copilot…) follows it.

## Install — one file, any machine

Run this in your repo (works on Windows, macOS, and Linux):

```bash
curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md -o AGENTS.md
```

Commit it. That's the whole setup — every agent that reads `AGENTS.md` now
follows the protocol. (No terminal? Just download
[`AGENTS.md`](https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md)
and drop it in your repo root.)

## What your agent does now

Before touching code, it becomes the right senior and opens its reply with a
verdict you can trust:

```text
Sage · backend · billing
Ikigai — needed: yes · lasts: extends RefundService · safe: touches settlement · agreed: idempotency required
Risk: HIGH — payment mutation
Decision: ask
```

…then it reuses your existing services, follows your team's rules, and stops on
`ask` / `reject` instead of charging ahead.

## Your rules, as Markdown

Knowledge lives in `agents/sage/<domain>/` — plain Markdown with a little YAML:

```markdown
---
title: Use idempotency keys
domain: billing
status: approved
enforcement: block        # block | warn | advise
---
All payment calls MUST pass an idempotency key. No exceptions.
```

Edit a rule, commit, done — the agent follows your version. When you tell it a
new rule in chat, it writes one as `status: proposed`; you approve by flipping it
to `approved`. It even keeps a library of senior personas in `agents/sage/roles/`.

## Works with every agent

`AGENTS.md` is read natively by **Claude Code, Codex, OpenCode, Antigravity**.
For **Cursor, Windsurf, Cline, Copilot, Gemini**, drop in a one-line adapter from
[`integrations/`](integrations/) — each just points the tool at `AGENTS.md`.

---

MIT — see [LICENSE](LICENSE). · [sage.qorstack.com](https://sage.qorstack.com)
