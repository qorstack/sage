<p align="center"><img src="assets/logo-full.png" alt="Sage" width="320"></p>

<h1 align="center">Sage</h1>

<p align="center"><b>Make your AI code like your most senior dev.</b></p>

Sage is a cognition protocol in a single **`AGENTS.md`**. Drop it in your repo and
any agent — Claude Code, Cursor, Codex, Copilot — reads your team's rules, weighs
the risk, and reuses what already exists **before** it writes a line. No install,
no server, no Python. Just Markdown you can read, edit, and `git push`.

## Install — one file

```bash
curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md -o AGENTS.md
```

Commit it. That's the whole setup — every agent that reads `AGENTS.md` now follows
the protocol.

```bash
# optional: start from the example knowledge instead of a blank slate
git clone --depth 1 https://github.com/qorstack/sage t && cp -r t/agents . && rm -rf t
```

## What your agent does now

Before touching code, it follows the pipeline in `AGENTS.md` and opens its reply
with a verdict you can trust:

```text
Risk: HIGH — payment mutation; touches settlement + webhook retry.
Decision: ask — payment rules require idempotency + an approved refund path.
```

…then it reuses your existing services, follows your team's rules, and stops on
`ask` / `reject` instead of charging ahead.

## 生き甲斐 — code with intention

Ikigai is the balance of four questions a senior asks before writing a line —
so Sage makes every agent ask them too, and answer them up front:

| | |
| --- | --- |
| **Is it needed?** | …or does something already cover it? |
| **Will it last?** | worth maintaining, in the shape the codebase already follows? |
| **Is it safe?** | what's the blast radius — money, auth, data? |
| **Did we agree?** | does it respect the rules in `agents/sage/`? |

## Your rules, as Markdown

Knowledge lives in `agents/sage/<domain>/` — plain Markdown with a little YAML:

```markdown
---
title: Use idempotency keys
domain: payment
status: approved
enforcement: block        # block | warn | advise
---
All payment calls MUST pass an idempotency key. No exceptions.
```

Edit a rule, commit, done — the agent follows your version. When you tell the agent
a new rule in chat, it writes one of these as `status: proposed`; you approve by
flipping it to `approved`.

## Works with every agent

`AGENTS.md` is read natively by **Claude Code, Codex, OpenCode, Antigravity**. For
**Cursor, Windsurf, Cline, Copilot, Gemini**, drop in a one-line adapter from
[`integrations/`](integrations/) — each just points the tool at `AGENTS.md`, so
there's one source of truth.

---

MIT — see [LICENSE](LICENSE). · [sage.qorstack.com](https://sage.qorstack.com)
