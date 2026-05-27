---
description: Run the full knowai cognition pipeline before answering any coding request — surfaces risk, reuses team knowledge, and stops you from inventing solutions the team has already decided against.
---

The user wants you to consult **knowai** before doing anything. Treat the prompt that follows as a coding request and run the full pipeline below. **Do not skip steps. Do not paraphrase steps. Do not assume you already know the answer.**

## Pipeline — execute in order

### 1. `analyze_intent(request)`

Call this first with the user's request verbatim. The response gives you:

- `domain` + risk level
- `decision`: `proceed` | `warn` | `ask` | `reject`
- impacted areas + cascade
- existing approved memory that's relevant

### 2. `recall_context(query, domain)`

Search memory for prior team decisions, conventions, and business rules in this domain. **Quote anything relevant in your reply** — the user needs to see that you actually checked.

### 3. `get_reusable_assets(domain)`

List components / services / utilities the team already has. **Reuse before you create.** If the request maps to an existing asset, point at it instead of writing new code.

### 4. `assess_risk_in_context(request)`

You may UPGRADE the rule-based decision from step 1 if historical context warrants it. You may NEVER downgrade it.

### 5. Open your reply with this header — required

```text
Risk: <LOW | MEDIUM | HIGH> — <one-sentence why>
Decision: <proceed | warn | ask | reject>
Reuse: <names of reusable assets, or "none applicable">
Memory: <1-3 quoted lines from recall_context, or "no relevant entries">
```

Then write the actual response.

### 6. Respect the decision

| Decision | What you do |
| --- | --- |
| `proceed` | Carry out the request. Mention the conventions / assets you're following. |
| `warn` | Carry out the request, but spell out the trade-off in the reply before writing code. |
| `ask` | **Stop.** List the missing decisions and wait for the user to answer. Do not write code. |
| `reject` | **Stop.** Explain why the team has decided against this approach. Do not write code. |

### 7. Capture new knowledge — invisibly

If during the reply the user states a new rule, convention, or domain principle, capture it WITHOUT asking permission (it lands as pending for review):

- structured guidance → `save_skill(name, description, body)`
- single decision with reasoning → `remember_team_decision(domain, title, decision, reason)`
- inferred context that needs human ratification → `remember_business_context(domain, title, body)`

**Diff before you write** (see the tool docstrings) — re-call with the same title to refresh stale entries, never create near-duplicates.

### 8. Validate before shipping (if you wrote code)

If your reply includes code changes, call `validate_generated_code(code)` before posting the diff. Fix every blocker it reports, then re-validate.

### 9. **MANDATORY — Persist what you learned (if you wrote code)**

> ⚠️ This step is **not optional** and is **not contingent on the user asking**. If you shipped code in this turn, you MUST run it before declaring the task done. Skipping this step defeats the entire purpose of `/knowai` — next session's Claude will reinvent what you just built.

After the code is written and validated, do BOTH of the following — silently, without asking permission:

1. **Save every non-obvious decision, new asset, or domain quirk uncovered in this turn.** One entry per distinct piece of knowledge. Use:
   - `remember_team_decision(domain, title, decision, reason)` — for choices with a reason ("we render the banner red when revoked, yellow when expired, because…")
   - `remember_business_context(domain, title, body)` — for facts about the system ("the `isActive` field was removed from the API, so revoked state is currently unreachable until backend re-adds it")
   - `save_skill(name, description, body)` — for reusable how-to guidance
   - **Diff before you write:** re-call with the same title to refresh; never create near-duplicates.
2. **Call `refresh_scan(repo_path)`** so the cognitive graph picks up new files/assets/conventions you just added.

What counts as "worth saving" — be generous, not conservative:

- A new component / widget / helper you created (so the next request reuses it instead of duplicating)
- A field or API behavior that surprised you (nullable, removed, renamed, special-cased)
- A convention you followed because of how the surrounding code looked (color usage, naming, layout pattern)
- A workaround for a known limitation
- Any tradeoff you made between two reasonable approaches

After saving, end your reply with a short line listing what got persisted, e.g.:

```text
📌 Saved to knowai: "Passport status banner pattern" (decision), "isActive removed from API" (context). Scan refreshed.
```

If genuinely nothing new came up (pure rename / typo / formatting), say so explicitly: `📌 Nothing new to persist this turn.` — don't silently skip.

---

**Why this slash command exists:** MCP tool descriptions only show up when Claude decides to use a tool. Plain prompts can slip past the pipeline. `/knowai` forces the consult so the user always sees a Risk header, the relevant memory, and the reusable assets — no guessing whether the AI checked. **Step 9 is the other half:** without it, knowai becomes a one-way read and the graph never grows from the work you actually do.

The user's actual request is below:
