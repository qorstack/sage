# /sage-unit-test — write unit tests that match how this repo already tests

Write meaningful unit tests for a target (a function, module, class, endpoint,
component) that **run and pass**, cover the behaviour that matters, and look like
the tests the team already writes. This skill is **language- and
framework-agnostic**: it detects the repo's test stack and mirrors it — it never
imposes a framework of its own.

Tests prove behaviour, not the mere existence of code. A test that can't fail, or
only asserts "it renders", is not worth writing.

> **Invoked by the run checklist.** When `unit-test` is active (§0 of `AGENTS.md`),
> Sage runs this itself for the logic it added or changed. It **authors new unit
> tests**; the core `automate-test` step **runs the whole existing suite** and
> reports the result; `/sage-e2e-test` covers **end-to-end / browser** testing.

---

## Model & effort — read the session ceiling first

Same discipline as `/sage`: detect the session **model + effort** and never
exceed either. Most test authoring sits at or just below the ceiling — designing
which cases matter needs judgment; typing them out does not. Drop to the floor
for purely mechanical additions (one more assertion in an existing test); stay at
the ceiling when reasoning about edge cases, boundaries, and failure modes. State
the ceiling once in the intent block.

---

## Step 1 — Load role (`qa`)

Open `agents/sage/roles/role-qa.md`:

- **Found** → read and adopt. Output: `Role: qa [loaded]`
- **Missing** → create it (persona: loves finding the input that breaks the code;
  good at boundary/equivalence analysis, choosing the smallest set of tests that
  covers the most behaviour, testing contracts not internals), output:
  `Role: qa [created]`

> **Multi-repo:** anchor knowledge (`agents/sage/`) to the repo that owns the
> code under test. State it once in the intent block.

---

## Step 2 — Detect the test stack (never assume)

Read the repo, don't guess:

1. **Framework + runner** — from config/manifest and existing tests. E.g.
   Jest/Vitest/Mocha (JS/TS), Pytest/unittest (Python), `go test` (Go),
   JUnit/TestNG (Java), RSpec/Minitest (Ruby), xUnit/NUnit (.NET), Cargo test
   (Rust), PHPUnit, etc. Use exactly what the repo uses.
2. **Conventions in practice** — open 2–3 existing test files near the target and
   copy their style: file location + naming (`*.test.ts` vs `*_test.go` vs
   `test_*.py`), import setup, describe/it vs table-driven, assertion library,
   fixture/factory helpers, mock/stub/spy approach, how async is awaited, how
   snapshots are used (or avoided).
3. **Run command** — how the suite is invoked (script in the manifest, Makefile,
   task runner). You will need this to actually run what you write.
4. **The unit's contract** — open the target and read its real signature,
   inputs, outputs, thrown errors, side effects, and dependencies. Never infer
   behaviour from the name. Identify the seams where external deps (network, db,
   clock, randomness, filesystem) must be controlled.

If there is **no existing test setup**, stop and ask which framework to add
(propose the ecosystem-standard one) before writing — adding a test toolchain is
a decision the human should make.

---

## Step 3 — Plan the cases, then state intent

Design the smallest set of tests that covers the behaviour. For the target,
enumerate:

- **Happy path** — the normal expected input → expected output.
- **Boundaries** — empty, zero, one, max, off-by-one, first/last, overflow.
- **Equivalence classes** — one representative per distinct behaviour, not 20
  near-duplicates.
- **Error paths** — every thrown error / rejected promise / non-happy return;
  invalid input; permission/validation failures.
- **State & side effects** — was the record written, the event emitted, the
  dependency called with the right args, the money computed correctly.
- **Contract, not internals** — assert on observable outputs and interactions,
  not private fields. Refactors that preserve behaviour must not break the test.

Then output the intent block and wait for `ask`/`reject`:

```text
Repo    : <repo-root>
Role    : qa — unit tests for <target>
Model   : <model> @ effort:<effort>  ← session ceiling
Stack   : <framework + runner> (detected)
Target  : <file:symbol> — <what it does>
Cases   : <n happy> + <n boundary> + <n error> + <n side-effect>
Mocks   : <deps to stub: network/db/clock/random/…>
Risk    : LOW | MEDIUM | HIGH
Decision: proceed | ask | reject
```

---

## Step 4 — Write the tests

- **Match the repo's style exactly** — same framework, file location, naming,
  assertion lib, and structure as the neighbours you read in Step 2.
- **Arrange–Act–Assert** (or given–when–then) — one clear behaviour per test,
  named so the name states the expectation (`returns 409 when an item is already
submitted`, not `test submit 2`).
- **Control all non-determinism** — mock/inject the clock, randomness, network,
  db, filesystem, and external services at their seam. No real network or wall
  clock. Tests must be deterministic and order-independent.
- **Assert real values** — exact outputs, exact error type/message, exact call
  arguments. Avoid assertions that can't fail (`expect(true).toBe(true)`,
  snapshotting everything).
- **One logical concept per test**; use table-driven/parametrized cases when the
  framework idiom supports it and the inputs are homogeneous.
- **No test interdependence** — each sets up and tears down its own state.
- Keep helpers/fixtures in the repo's existing helper location; don't invent a
  parallel structure.

---

## Step 5 — Run them and prove it (mandatory)

Never claim the tests pass without evidence.

1. Run the narrowest scope first (the single new test file), then the surrounding
   suite if the change could affect it, using the repo's real run command.
2. Show the actual result — pass/fail counts, and any failure output.
3. If a test fails: decide whether the **test** is wrong (fix it) or it found a
   **real bug** in the target (report it clearly — do not silently weaken the
   test to make it green). Weakening a test to pass is a failure of this skill.
4. Confirm the tests actually exercise the target (they fail if you break the
   target) — mutation-check the critical assertion mentally, or briefly, when
   correctness is high-risk.

---

## Step 6 — Capture knowledge (mandatory)

- **A — New** testing convention worth reusing →
  `agents/sage/<domain>/decisions/<slug>.md` (pattern + why + Do/Avoid;
  `enforcement: advise`, `source: ai`, `status: proposed`). E.g. "Mock the API
  client at the axios-instance seam, not per-endpoint" or "Use table-driven
  cases for validators."
- **B — Updated** an existing testing decision → update in place.
- **C — None** → `No new knowledge — <file> covers this`.

If the repo has no test-conventions decision yet and you just established one,
prefer to write it (option A) so the next run is consistent.

---

## Step 7 — Summary (mandatory — a response without this is incomplete)

Output as plain markdown (no code fence):

```markdown
── Sage Unit Test ────────────────────────────────
**Role** · qa — unit tests for <target>
**Model** · <model> @ effort:<effort>
**Stack** · <framework + runner> | **Risk** · <LOW|MEDIUM|HIGH>

**Written**
List the test files created/updated and how many cases each holds, grouped by
happy / boundary / error / side-effect.

**Coverage of behaviour**
State which behaviours are now covered and which are deliberately out of scope
(and why) — coverage of behaviour, not just a line %.

**Ran**
The exact command run and the real result (e.g. `pnpm test path — 14 passed`).
If anything failed, say what and what you did about it.

**Bugs found**
Any real defects the tests surfaced in the target (or "none").

**Knowledge** · [new | updated | none] `<path>` — <pattern title>
──────────────────────────────────────────────────
```

Then stop.
