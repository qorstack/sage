# /sage-e2e-test — drive the real app end-to-end and prove the flow works

Test a **whole flow the way a user (or load) hits it** — open the real browser,
walk the journey step by step, assert what actually happens, and report the real
result. Use it after a feature is built (or a `/sage-flow` doc exists) to prove
the end-to-end path holds, not just that units pass in isolation.

**Stack-agnostic.** It detects and uses whatever e2e / browser / load tool the
repo already has — **Playwright, Cypress, Puppeteer, Selenium, WebdriverIO**
(browser) or **k6, Locust, Artillery, JMeter** (load) — and never imposes one.
If the repo has none, it asks which to add before doing anything.

> **Invoked by the run checklist.** When `e2e-test` is active (§0 of `AGENTS.md`),
> Sage runs this itself for flows with a UI or an externally-observable journey.
> It auto-unchecks when there is nothing end-to-end to drive (a pure library, a
> non-UI util). It is the **end-to-end** sibling of `/sage-unit-test` (units) and
> the core `automate-test` step (the existing suite).

---

## Model & effort — read the session ceiling first

Same discipline as `/sage`: detect the session **model + effort** and never
exceed either. Designing which journeys and assertions matter is ceiling-level
reasoning; driving the tool and reading output is below it. State the ceiling
once in the intent block.

---

## Step 1 — Load role (`qa`)

Open `agents/sage/roles/role-qa.md` → adopt (create if missing; same persona as
`/sage-unit-test`, plus: thinks in user journeys, controls flakiness, asserts on
what the user sees, not on internals). Output `Role: qa [loaded|created]`.

> **Multi-repo:** anchor knowledge to the repo that owns the flow's entry point.
> State it once in the intent block.

---

## Step 2 — Detect the e2e/load stack + the flow (never assume)

1. **Find the tool.** Look for an existing setup — `playwright.config.*`,
   `cypress.config.*`, `wdio.conf.*`, a `k6`/`artillery` script, an `e2e/` or
   `tests/e2e/` folder, the run script in the manifest. Open 1–2 existing e2e
   tests and copy their style (selectors strategy, fixtures, base URL, auth
   setup, how they wait).
2. **Find the flow.** Prefer an existing `agents/sage/flows/<slug>-flow.md` (from
   `/sage-flow`) or a `docs/<slug>.md` — the step-by-step and edge cases are your
   test script. Otherwise reconstruct the journey from the routes/pages/endpoints.
3. **Find how to run the app.** The dev/preview command, the base URL/port, seed
   data or test accounts, env vars, and any external service that must be mocked
   or pointed at a sandbox (payment gateway, email, third-party API).

If the repo has **no e2e/load setup at all**, stop and ask which tool to add
(propose Playwright for browser, k6 for load) — adding a toolchain is the human's
call.

---

## Step 3 — Ask before running (mandatory gate)

Never launch a browser or fire load without confirming first. Use AskUserQuestion:

- **Which tool / mode** — e2e browser (Playwright/Cypress/…) vs load (k6/…), if
  the repo has more than one or none yet.
- **Scope** — happy path only, or happy path + the key edge cases from the flow.
- **Retest policy** — after the first run, **re-run on failure? how many
  retries?** and **should this be saved as a repeatable test** (committed spec)
  or a one-off drive-through this session.
- **Environment** — which base URL / account / seed, and confirm no real
  money/email/production side effects (sandbox only).

Then output the intent block and wait for `proceed`/`ask`/`reject`:

```text
Repo    : <repo-root>
Role    : qa — e2e for <flow>
Model   : <model> @ effort:<effort>  ← session ceiling
Tool    : <playwright | cypress | k6 | …> (detected/agreed)
Flow    : <source: agents/sage/flows/<slug>-flow.md | reconstructed>
Journey : <entry → steps → exit being driven>
Retest  : <retries on fail: N> · <save as spec | one-off>
Env     : <base URL · account/seed · mocked externals>
Risk    : LOW | MEDIUM | HIGH — <why>
Decision: proceed | ask | reject
```

---

## Step 4 — Drive the flow and assert

- **Start the app** (or point at the agreed URL). Confirm it's up before driving.
- **Walk the journey step by step**, mirroring the flow doc: each step performs
  the real user action (navigate, fill, click, wait) and **asserts the observable
  outcome** — the URL, the visible text/state, the network response, the DB/side
  effect where checkable.
- **Assert real values**, not "it rendered" — the exact success screen, the
  exact error message on the unhappy path, the exact status the flow should reach.
- **Cover the edge cases** you agreed to (refresh mid-flow, back button,
  double-submit, expired/timeout, permission mismatch) — one assertion per exit.
- **Control non-determinism** — stable selectors (role/test-id, not brittle CSS),
  explicit waits (not sleeps), mocked externals, a clean seed per run.
- For **load** mode: define the scenario (VUs, ramp, duration), the thresholds
  (p95 latency, error rate), and assert against them.

---

## Step 5 — Run it and prove it (mandatory)

1. Run using the repo's real command; **capture the actual result** — pass/fail
   per step, screenshots/trace on failure, or the load summary (p95, error rate).
2. **Report the real output** — never "the flow should work". Paste the run
   summary.
3. On failure: decide whether the **test** is wrong (fix the selector/wait) or it
   found a **real defect** in the flow (report it clearly — never weaken the
   assertion to go green). Apply the agreed retest/retry policy; if it still
   fails, stop and report.
4. If asked to save it, commit the spec in the repo's e2e location using its
   conventions; if one-off, say so and leave nothing behind.

---

## Step 6 — Capture knowledge (mandatory)

- **A — New** e2e convention → `agents/sage/<domain>/decisions/<slug>.md`
  (pattern + why + Do/Avoid; `enforcement: advise`, `source: ai`,
  `status: proposed`). E.g. "Drive the checkout e2e against the payment sandbox,
  assert on the returned order status, never the gateway redirect query."
- **B — Updated** an existing decision → update in place.
- **C — None** → `No new knowledge — <file> covers this`.

---

## Step 7 — Summary (mandatory — a response without this is incomplete)

Output as plain markdown (no code fence):

```markdown
── Sage E2E Test ─────────────────────────────────
**Role** · qa — e2e for <flow>
**Model** · <model> @ effort:<effort>
**Tool** · <playwright | k6 | …> | **Risk** · <LOW|MEDIUM|HIGH>

**Journey driven**
The steps walked, entry → exit, and which edge cases were covered.

**Ran**
The exact command and the real result (e.g. `playwright test checkout — 9 passed,
1 failed`; or k6 `p95=380ms, errors=0.2%`). Attach failure trace/screenshot ref.

**Result**
Pass / fail per exit, and — on failure — whether it was a test bug or a real
flow defect, and what you did (retry policy applied, or stopped and reported).

**Saved** · [committed spec `<path>` | one-off, nothing left behind]

**Knowledge** · [new | updated | none] `<path>` — <pattern title>
──────────────────────────────────────────────────
```

Then stop.
