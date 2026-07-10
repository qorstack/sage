# /sage-learning — learn this codebase + research best practices into Sage knowledge

Two things in one run, because they belong together: **(1) learn how this team
already writes code** and capture it as rules/decisions, then **(2) research the
current best practices for this stack** and capture them as skills. Together they
give the next agent both the team's real conventions and the wider community's
proven patterns. Run once per repo, and again after big refactors or a stack
change.

Everything you find is saved to `agents/sage/` **in the repo** — never to local
memory, never to a scratch file. Format: `AGENTS.md` §2. Diff before writing
(`AGENTS.md` §3): never duplicate an existing entry; update a stale one in place;
one idea per file.

---

## Phase 1 — Learn from THIS codebase

**Role: `codebase-analyst`** — open `agents/sage/roles/role-codebase-analyst.md`;
if missing, create it (expertise: reading source, extracting real conventions,
spotting reusable assets; pitfall: inventing conventions the code doesn't follow).
Output `Role: codebase-analyst [loaded|created]`.

1. **Map the repo.** Identify the domains (e.g. `billing`, `search`), the stack
   (detect from real manifests — `package.json`, `pyproject.toml`, `go.mod`,
   `Cargo.toml`, `pom.xml`, `*.csproj`, `composer.json`, `Gemfile`, `pubspec.yaml`,
   …; never assume JS/web), and the conventions actually in use — naming, error
   handling, folder layout, logging, testing, the patterns the team repeats.

2. **Find the reusable assets and read them — do not guess.** Services, utils,
   components, base classes, generated clients, test helpers the team already has.
   For each: **open the file and read its exports** (signatures, params, options,
   return types — only the source is authoritative), document the full API in the
   matching `decisions/<slug>.md` (a table of every exported symbol + purpose +
   key options), and flag when an asset covers more than its name suggests.

3. **Spot the rules-in-practice.** What does the code consistently do (and avoid)?
   Each consistent pattern is a candidate rule.

4. **Write it to `agents/sage/`:** per-domain `rules.md` (conventions + reusable
   assets), `decisions/<slug>.md` for notable patterns (`enforcement: advise`
   unless clearly a must, `source: ai`, `status: proposed`), and enrich each
   `roles/role-<lens>.md` → its **Expertise** with the stack/patterns you found.

   Write the **pattern**, not the implementation:
   - Good: "Team uses Zod for all API response validation."
   - Bad: "In user-service.ts we used z.string() on line 42."

---

## Phase 2 — Research best practices for the stack

**Role: `researcher`** (handoff) — open `agents/sage/roles/role-researcher.md`;
if missing, create it (expertise: evaluating sources, distilling opinionated
guidance from noise, matching patterns to a specific stack; pitfall: cargo-culting
advice that doesn't fit this stack). Output
`Role: researcher [loaded|created] — handoff from codebase-analyst`.

1. **Use the stack + domains** detected in Phase 1 (plus the existing
   `agents/sage/` knowledge, so you don't duplicate it).

2. **Research current best practices** for this exact stack — use web search if
   available. Focus on what's specific and opinionated, skip well-known
   boilerplate:

   | Category               | What to look for                                             |
   | ---------------------- | ------------------------------------------------------------ |
   | Patterns for the stack | composition, state colocation, accessibility, design tokens  |
   | Minimal code           | YAGNI, single-responsibility, avoiding premature abstraction |
   | Code quality           | naming, error handling, type safety, test strategy           |
   | Performance            | bundle size, lazy loading, query patterns, caching           |
   | Trending               | patterns gaining adoption in the last ~12 months             |

3. **Write skill entries** at `agents/sage/<domain>/skills/<slug>.md` — one idea
   per file (three sub-rules → three files), `type: skill`, `enforcement: advise`
   unless a well-established must, `source: ai`, `status: proposed`:

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

   <one paragraph: what, why, and when>

   **Do:**

   - concrete example or rule

   **Avoid:**

   - anti-pattern or counter-example
   ```

If web search is unavailable, say so and skip Phase 2 (Phase 1 still runs).

---

## Summary (mandatory — a response without this is incomplete)

Output as **plain markdown** (no code fence):

```markdown
── Sage Learning ─────────────────────────────────
**Stack** · <language, framework, key libs>
**Domains** · <list of domains>

**From the codebase**

- [new] `agents/sage/<domain>/decisions/<slug>.md` — <pattern title>
- [updated] `agents/sage/<domain>/rules.md` — <what changed>
- [skipped] `<file>` — already covered by `<existing-entry>`

**From research**

- `agents/sage/<domain>/skills/<slug>.md` — <title>
- (or: research skipped — no web search available)

**Next** · flip `status: approved` on entries you want enforced
──────────────────────────────────────────────────
```
