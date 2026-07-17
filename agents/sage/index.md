# Sage knowledge

This folder is your team's knowledge — the rules and decisions Sage's agent
reads before it writes code (see [`../../AGENTS.md`](../../AGENTS.md)).

**It starts empty on purpose.** Add domains as your project needs them — there
are no generic, pre-baked rules to delete. Sage's agent also fills this in for
you: when you state a rule in chat, it writes one here as `status: proposed`.

## Layout

```text
agents/sage/
  index.md                  # this file
  commands/<name>.md        # canonical command bodies — the tool adapters point here
  docs-style-template.md    # the /sage-docs + /sage-flow markdown style-guide
  flows/<slug>-flow.md      # implementation-ready flow docs from /sage-flow
  roles/role-<lens>.md      # reusable senior personas (ikigai roles) — see AGENTS.md §2
  <domain>/                 # e.g. billing, search, your own domains
    rules.md                # the domain's standing rules
    decisions/<slug>.md     # one team decision per file
```

`commands/` holds every Sage command in full, once; the per-tool files under
`integrations/` are thin pointers to it, so editing a command in one place
updates every agent.

`flows/risk-controls-flow.md` defines the current end-to-end contract for turning
risk drivers into required controls, validation evidence, and residual risk.

`roles/` is Sage's library of senior personas — each one an **ikigai role** that
knows what it's good at. Sage creates them as topics come up and reuses them
after (`roles/role-dev.md` ships as a starter example).

## Example entry

`agents/sage/billing/decisions/use-ledger-service.md`:

```markdown
---
title: Use the Ledger service for money movement
domain: billing
status: approved
enforcement: block
applies_to: [billing, "billing/**"]
source: human
---

All money movement goes through `ledger.transfer()`. Never call the payment
provider SDK directly — it bypasses our audit trail.
```

Edit a file, commit, done — the agent follows your team's version.

## Domains

- [frontend](frontend/) - static pages, UI, responsive layout, and landing-page design.
- [protocol](protocol/) - Sage cognition policy, risk controls, and cross-command contracts.
