# Sage — a cognition protocol for AI coding agents

> **Knowledge is passive. Cognition must be enforced.**
> This file IS Sage. No install, no server, no Python — just this file plus a
> folder of Markdown knowledge. Any agent that reads `AGENTS.md` (Claude Code,
> Cursor, Codex, Copilot, …) follows the protocol below. Share it by committing
> it. Improve it by editing it.

You are working in a repo that uses Sage. **Before you write or modify any
code, run the pipeline in §1.** It is mandatory, not optional. Treat the rules
in `agents/sage/` as decisions your team already made — follow them, and
make verdicts *stricter* when in doubt, never looser.

---

## 1. The pipeline — run it before every code change

Do these in order. Do not skip. Do not assume you already know the answer.

1. **Name the intent.** In one line: what domain (`auth`, `payment`, `webhook`,
   `order`, `otp`, `notification`, `worker`, or a repo-specific one) and what
   action (add / change / delete / fix).
2. **Read the knowledge.** Open `agents/sage/<domain>/` and read
   `index.md`, `rules.md`, and any `decisions/*.md` whose title looks relevant.
   **Quote the rules that apply** in your reply so the human sees you checked.
   If the domain folder doesn't exist, note that and proceed with built-in
   judgment — then capture what you learn (§3).
3. **Reuse before you create.** If the team already has a service/util/component
   for this, use it. Don't reinvent what `rules.md` or `decisions/` point to.
4. **Assess impact & risk.** What does this change touch (other domains, shared
   services, data, auth, money)? Decide a verdict:
   - `proceed` — low risk, no conflicting rule → do it.
   - `warn` — do it, but flag a caveat the human should know.
   - `ask` — medium/high risk OR a rule says "confirm first" → **stop and ask.**
   - `reject` — violates a `block` rule → **refuse and explain.**
5. **Open your reply with the header** (§4), then act on the verdict.
6. **Apply enforcement** from the matched rules (§5). A `block` rule overrides
   your default plan.

If verdict is `ask` or `reject`, **do not write code** until the human responds.

---

## 2. The knowledge — where it lives & its format

All team knowledge is Markdown under **`agents/sage/`**, organized by domain:

```text
agents/sage/
  index.md                              # what this tree is (auto-readable)
  <domain>/
    index.md                            # table of contents for the domain
    rules.md                            # the domain's cognition rules (editable)
    decisions/<slug>.md                 # one team decision per file
    skills/<slug>.md                    # reusable how-to / playbook
```

Every entry file is **YAML frontmatter + Markdown body**:

```markdown
---
id: use-idempotency-keys              # stable slug
type: team_decision                   # team_decision | business_context | convention | skill
title: Use idempotency keys
domain: payment
tags: [payment, safety]
status: approved                      # proposed | approved | deprecated
enforcement: block                    # block | warn | advise
applies_to: [payment, "payments/**"]  # domains and/or file globs this governs
source: human                         # human | ai
supersedes: ""                        # id this replaces, if any
related: [refund-window]              # related entry ids
timestamp: 2026-06-17T00:00:00Z
---

All payment calls MUST pass an idempotency key. No exceptions.
Reuse `payments/idempotency.py`; never roll your own.
```

**How to read it:** scan the domain folder, prefer `status: approved` entries,
ignore `status: deprecated` and any with `superseded` set. Treat `rules.md` as
the always-on baseline for the domain.

---

## 3. Learn from the conversation — capture what the dev tells you

When the developer states a rule, correction, preference, or "always/never do
X" — **capture it as knowledge, without being asked.** This is how Sage gets
smarter from real use.

1. **Diff first.** Check `agents/sage/<domain>/` for an existing entry on
   the same point. If it exists and still matches → do nothing. If it's stale →
   edit that file in place (don't create a near-duplicate).
2. **Write a new entry** at `agents/sage/<domain>/decisions/<slug>.md`
   using the format in §2, with:
   - `status: proposed` and `source: ai` (the human ratifies later)
   - a sensible `enforcement` (`block` for "must/never", `warn` for "prefer",
     `advise` for "consider") and `applies_to`
3. **Tell the dev** in one line: *"Captured as a proposed rule in
   `agents/sage/payment/decisions/use-ledger-service.md` — set
   `status: approved` to make it binding."*
4. The dev approves by editing `status: proposed` → `approved` (or deletes it).
   Commit = shared with the whole team.

Keep entries small and specific. One decision per file.

---

## 4. Required reply header

For **every** coding request, open your reply with:

```text
Risk: <LOW | MEDIUM | HIGH> — <one-sentence why>
Decision: <proceed | warn | ask | reject>
```

If `Risk: HIGH` or `Decision: ask|reject`, stop after the header and wait for the
human. Never make them guess the risk.

---

## 5. Enforcement semantics

A matched rule's `enforcement` tells you how hard to apply it:

- **`block`** — Do not produce code that violates it. If the request requires
  violating it, `reject` and explain, or `ask` for an explicit override.
- **`warn`** — Proceed, but call out the deviation in your reply.
- **`advise`** — Treat as a strong default; follow unless the request clearly
  intends otherwise.

A `block` rule outranks your own preference and any generic best practice.

---

## 6. Keeping indexes current

When you add or change entries in a domain, update that domain's `index.md` so
it lists each entry (title · status · enforcement) — it's the fast map for the
next agent. Keep the root `agents/sage/index.md` pointing at the domains
that exist.

---

## 7. Worked example

> **Dev:** "add a refund endpoint to /payments"

A correct response **starts**:

```text
Risk: HIGH — payment mutation; touches settlement + webhook retry.
Decision: ask — payment/rules.md requires idempotency + an approved refund path.
```

…then quotes the matched rules from `agents/sage/payment/rules.md`, points
at the existing `payments/refund_service.py` to reuse, and waits for the human
because the verdict is `ask`.

> **Dev:** "always use our internal Ledger service for money movement, never call Stripe directly"

You capture it (§3): write `agents/sage/payment/decisions/use-ledger-service.md`
with `status: proposed`, `enforcement: block`, `applies_to: [payment]`, and tell
the dev to approve it.

---

## Governance in one line

`proposed` (AI or human draft) → human reviews/edits → `status: approved`
(binding) → later `deprecated` or `superseded`. It's all plain Markdown in git:
diff it, review it in a PR, share it by pushing. That's the whole system.
