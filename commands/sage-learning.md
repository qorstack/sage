# /sage-learning — learn this codebase into Sage knowledge

Study how **this team actually writes code** and turn it into Sage knowledge, so
every future agent writes code that matches them. Run once per repo, and again
after big refactors. Everything you find is saved under `agents/sage/`.

Do this:

1. **Map the repo.** Identify the domains (e.g. `billing`, `search`), the stack,
   and the conventions actually in use — naming, error handling, folder layout,
   logging, testing, the patterns the team repeats.
2. **Find the reusable assets.** Services, utils, components, base classes the
   team already has — what new code should reuse instead of reinventing.
3. **Spot the rules-in-practice.** What does the code consistently do (and
   avoid)? Each consistent pattern is a candidate rule.
4. **Write it to `agents/sage/`** (format in `AGENTS.md` §2):
   - per-domain `rules.md` — the conventions + reusable assets for that domain;
   - `decisions/<slug>.md` for notable patterns worth enforcing
     (`enforcement: advise` unless it's clearly a must), `source: ai`,
     `status: proposed`;
   - update `roles/role-<lens>.md` → its `Good at` with the stack/patterns you found.
5. **Diff before writing** (`AGENTS.md` §3): never duplicate an existing entry;
   update a stale one in place. One idea per file.

Then tell the dev what you captured, in one list. They review and flip
`status: approved`. This is how Sage learns to code like the team — re-run it
whenever the codebase shifts.
