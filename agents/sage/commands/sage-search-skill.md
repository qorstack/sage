# /sage-search-skill — research best practices and write them as team skills

Scan this project's stack and domains, research current best practices and
trending patterns relevant to it, then write the findings as reusable skill
entries under `agents/sage/`. Run this once when starting on a new repo, or
whenever the team wants a knowledge refresh.

---

## Role (fixed — `researcher`)

Open `agents/sage/roles/role-researcher.md` before starting:

- **Found** → read and adopt as-is. Output: `Role: researcher [loaded]`
- **Missing** → create it now, output: `Role: researcher [created]`

Default Ikigai if creating:

- Loves — finding what the community has learned so the team doesn't have to
- Good at — searching for current best practices, evaluating sources, distilling
  opinionated guidance from noise, matching patterns to a specific stack
- Team needs — up-to-date external knowledge without reading every blog post
- Worth it — skills that raise the team's baseline, written once, reused forever

---

## Step 1 — Map the project

Read the project's root config files (`package.json`, `pyproject.toml`,
`Cargo.toml`, `go.mod`, framework configs, etc.) and a sample of source files.
Identify:

- **Stack** — language, framework(s), UI library, test runner, build tool
- **Domains** — folder structure, main feature areas (e.g. `auth`, `api`, `ui`,
  `payments`)
- **Existing knowledge** — list what's already in `agents/sage/` so you don't
  duplicate it

## Step 2 — Research current best practices

Use web search (if available) to find current, widely-adopted best practices
for this exact stack. Focus on:

| Category                    | What to look for                                               |
| --------------------------- | -------------------------------------------------------------- |
| **UI / component patterns** | composition, accessibility, state colocation, design tokens    |
| **Minimal code**            | YAGNI, single-responsibility, avoiding premature abstraction   |
| **Code quality**            | naming, error handling, type safety, test strategy             |
| **Performance**             | bundle size, lazy loading, query patterns, caching             |
| **Trending**                | patterns gaining adoption in the last 12 months for this stack |

Prefer opinionated, specific guidance over generic advice. Skip anything that
is already well-known boilerplate.

## Step 3 — Write skill entries

For each meaningful finding, create or update a file at:

```
agents/sage/<domain>/skills/<slug>.md
```

Use this format:

```markdown
---
id: <slug>
type: skill
title: <short title>
domain: <domain>
status: proposed
source: ai
enforcement: advise
tags: [<tag>, ...]
---

<one-paragraph explanation of the practice — what, why, and when>

**Do:**

- concrete example or rule

**Avoid:**

- anti-pattern or counter-example
```

Rules:

- One idea per file. If a pattern has three sub-rules, write three files.
- `enforcement: advise` unless it's a well-established must-do for this stack.
- Never duplicate an entry that already exists in `agents/sage/`.
- Update a stale entry in place rather than creating a duplicate.

## Step 4 — Report

When done, output as **plain markdown** (no code fence):

```markdown
── Sage Search Skill ─────────────────────────────
**Stack** · <language, framework, key libs>
**Domains** · <list of domains updated>

**Skills written**

- `agents/sage/<domain>/skills/<slug>.md` — <title>

**Next** · flip `status: approved` on anything you want enforced
──────────────────────────────────────────────────
```

Then stop. The dev reviews and approves.
