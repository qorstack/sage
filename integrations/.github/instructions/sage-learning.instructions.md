---
applyTo: "agents/sage/**"
---

# Sage Learning

When asked to "learn this codebase" or run sage-learning:

Study how **this team actually writes code** and turn it into Sage knowledge, so
every future agent writes code that matches them. Run once per repo, and again
after big refactors. Everything goes to `agents/sage/` **in the repo** — never
to local memory.

1. **Map the repo.** Identify domains, the stack, and conventions in use —
   naming, error handling, folder layout, logging, testing, repeated patterns.
2. **Find the reusable assets and read them — do not guess.** For each asset:
   - **Open the file and read its exports** — signatures, parameter shapes,
     return types. Never infer from the file name; only the source is authoritative.
   - Document the full API in `decisions/<slug>.md` (exported symbols + purpose).
   - Flag assets that cover more use-cases than their name suggests.
3. **Spot the rules-in-practice.** Each consistent pattern is a candidate rule.
4. **Write it to `agents/sage/`** (format in `AGENTS.md` §2):
   - per-domain `rules.md`; `decisions/<slug>.md`; update relevant role files.
   - Write the **pattern**, not the implementation — rules must apply next time.
5. **Diff before writing**: never duplicate an existing entry; update in place.

**A response without this block is incomplete.** Close with:

```text
── Sage Learning ─────────────────────────────────
Stack     : <language, framework, key libs>
Domains   : <list of domains found>
Written   :
  [new]     agents/sage/<domain>/decisions/<slug>.md — <pattern title>
  [updated] agents/sage/<domain>/rules.md — <what changed>
  [skipped] <file> — already covered by <existing-entry>
Next      : flip status: approved on entries you want enforced
──────────────────────────────────────────────────
```
