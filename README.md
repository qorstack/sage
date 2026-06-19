<p align="center"><img src="assets/logo-full.png" alt="Sage" width="640"></p>

<h1 align="center">Sage</h1>

<p align="center"><b>Make your AI code like your most senior dev.</b></p>

## The Sage

Every team has a senior who has seen it all — the one who, before touching
anything, quietly asks: _Is this even needed? Will it last? Is it safe? Did we
already agree on this?_ That balance of purpose and care has a name in Japan:
**生き甲斐 — ikigai**, your reason for doing.

Sage gives that senior's ikigai to **every AI agent you use**. Before it writes
a line, the agent becomes the right kind of senior for the task, weighs those
four questions against your team's rules, and _then_ codes — or stops and asks.

|     | the question      |                                                           |
| --- | ----------------- | --------------------------------------------------------- |
| 🎯  | **Is it needed?** | …or does something already cover it?                      |
| ⏳  | **Will it last?** | worth maintaining, in the shape the code already follows? |
| 🛡️  | **Is it safe?**   | what's the blast radius — money, auth, data?              |
| 🤝  | **Did we agree?** | does it respect the rules in `agents/sage/`?              |

No install, no server, no Python. Sage is a cognition protocol in a single
**`AGENTS.md`** — Markdown you read, edit, and `git push`. Any agent that reads
`AGENTS.md` (Claude Code, Cursor, Codex, Copilot…) follows it.

## Install — one file, any machine

### Let your AI set it up

Paste this into any AI coding agent (Claude Code, Cursor, Copilot, Windsurf…):

```text
Set up Sage in this repo.

1. Fetch https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md
   and save it as AGENTS.md at the repo root.
2. Detect which AI tools this repo uses by checking for .claude/, .cursor/,
   .windsurf/, .clinerules/, .github/instructions/, or GEMINI.md.
   For each one found, fetch the matching adapter from
   https://raw.githubusercontent.com/qorstack/sage/main/integrations/<tool-path>
   and place it in the repo. If none are found, ask me which tool I use.
3. Fetch https://raw.githubusercontent.com/qorstack/sage/main/agents/sage/index.md
   and save it as agents/sage/index.md.
4. Tell me what was installed. Then list these three commands that are now
   available (explain each in one sentence):
   - /sage — run the cognition pipeline before any code change
   - /sage-learning — scan this codebase and write team knowledge to agents/sage/
   - /sage-search-skill — research best practices for this stack and add them as skills
   Finally, ask me: "Would you like me to run /sage-learning now to capture
   this codebase's patterns?"
```

Or install manually:

### 1. Copy the protocol

Run this in your repo (works on Windows, macOS, and Linux):

```bash
curl -fsSL https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md -o AGENTS.md
```

No terminal? Download
[`AGENTS.md`](https://raw.githubusercontent.com/qorstack/sage/main/AGENTS.md)
and drop it in your repo root.

### 2. Wire up your agent

**Claude Code, Codex, OpenCode, Antigravity** read `AGENTS.md` natively — nothing else needed.

For **Cursor, Windsurf, Cline, Copilot, Gemini**, copy the thin adapter for your tool:

| Tool | Command |
| --- | --- |
| Claude Code | `cp -r integrations/.claude .` |
| Cursor | `cp -r integrations/.cursor .` |
| Windsurf | `cp -r integrations/.windsurf .` |
| Cline | `cp -r integrations/.clinerules .` |
| GitHub Copilot | `cp -r integrations/.github .` |
| Gemini CLI | `cp integrations/GEMINI.md .` |

Each adapter is one line: "read and follow `AGENTS.md`." Edit the protocol in
one place and every agent stays in step.

### 3. Optionally seed starter knowledge

```bash
git clone --depth 1 https://github.com/qorstack/sage t && cp -r t/agents . && rm -rf t
```

Commit everything. That's the whole setup.

## Commands

Three commands cover the full lifecycle:

**`/sage`** — run the cognition pipeline before any code change

```text
/sage add stripe webhook handler

Role: backend — payments/webhooks
Ikigai: needed: yes / lasts: WebhookService / safe: financial data / agreed: idempotency required
Risk: HIGH — payment mutation
Decision: ask — I found payments/idempotency.py. Waiting for confirmation before editing.
```

**`/sage-learning`** — scan this codebase once and write team knowledge

```text
/sage-learning

Mapped 3 domains: api, auth, payments
Written: agents/sage/api/rules.md
Written: agents/sage/payments/decisions/idempotency-keys.md
12 rules captured — review and flip status: approved
```

**`/sage-search-skill`** — research current best practices for this stack and write them as skills

```text
/sage-search-skill

Stack detected: TypeScript + React + Tailwind
Researched: component patterns, accessibility, performance, 2025 trends
Written: agents/sage/frontend/skills/component-composition.md
Written: agents/sage/frontend/skills/avoid-premature-abstraction.md
Written: agents/sage/frontend/skills/server-component-boundaries.md
6 skills added — review and approve
```

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
enforcement: block # block | warn | advise
---

All payment calls MUST pass an idempotency key. No exceptions.
```

Edit a rule, commit, done — the agent follows your version. When you tell it a
new rule in chat, it writes one as `status: proposed`; you approve by flipping it
to `approved`. It even keeps a library of senior personas in `agents/sage/roles/`.

Run **[`/sage-learning`](commands/sage-learning.md)** once to seed `agents/sage/`
straight from your existing code — Sage studies the team's real patterns and
writes them up so future code matches.

## Works with every agent

`AGENTS.md` is read natively by **Claude Code, Codex, OpenCode, Antigravity**.
For **Cursor, Windsurf, Cline, Copilot, Gemini**, drop in a one-line adapter from
[`integrations/`](integrations/) — each just points the tool at `AGENTS.md`.

---

MIT — see [LICENSE](LICENSE). · [sage.qorstack.com](https://sage.qorstack.com)
