import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


class RequestRoutingProtocolTests(unittest.TestCase):
    def test_behavioral_fixture_covers_all_routes_and_core_boundaries(self) -> None:
        cases = json.loads(read("tests/fixtures/request_routing_cases.json"))
        routes = {case["expected_route"] for case in cases}
        invariants = {item for case in cases for item in case["invariants"]}

        self.assertEqual(
            routes,
            {
                "clear-single-session",
                "foggy-single-session",
                "large-multi-session",
            },
        )
        for required in (
            "do-not-grill",
            "run-sage-grill",
            "run-sage-wayfinder",
            "do-not-ask-fact",
            "human-answers-hitl",
            "update-context-inline",
            "reopen-only-with-new-evidence",
        ):
            with self.subTest(required=required):
                self.assertIn(required, invariants)

    def test_canonical_router_names_all_routes_and_is_checklist_independent(self) -> None:
        agents = read("AGENTS.md")
        sage = read("agents/sage/commands/sage.md")

        for route in (
            "clear-single-session",
            "foggy-single-session",
            "large-multi-session",
        ):
            with self.subTest(route=route):
                self.assertIn(route, agents)
                self.assertIn(route, sage)

        self.assertIn("independent of `plan-flow`", compact(agents))
        self.assertIn("independent of `plan-flow`", compact(sage))

    def test_grill_has_checkpoint_domain_model_and_exit_contract(self) -> None:
        grill = compact(read("agents/sage/commands/sage-grill.md"))

        for marker in (
            "before the first question",
            "context.md",
            "concrete boundary/counterexample",
            "A HITL decision is never answered by the agent",
            "requirements-clear",
            "must not ask a resolved product question again",
            "/sage-wayfinder",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, grill)

        context_contract = read("AGENTS.md")
        for field in ("**Definition:**", "**Invariants:**", "**Includes:**", "**Excludes:**"):
            with self.subTest(context_field=field):
                self.assertIn(field, context_contract)

    def test_wayfinder_has_durable_map_frontier_and_claim_contract(self) -> None:
        wayfinder = read("agents/sage/commands/sage-wayfinder.md")

        for marker in (
            "agents/sage/wayfinders/<slug>/map.md",
            "Destination",
            "Not yet specified",
            "Out of scope",
            "blocked_by",
            "assignee",
            "frontier",
            "No-fog early exit",
            "One session resolves at most one non-research ticket",
            "agents/sage/flows/<slug>-spec.md",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, wayfinder)

    def test_every_adapter_exposes_grill_and_wayfinder(self) -> None:
        adapters = {
            "claude": "integrations/.claude/commands/{name}.md",
            "codex": "integrations/.codex/prompts/{name}.md",
            "cline": "integrations/.clinerules/{name}.md",
            "cursor": "integrations/.cursor/rules/{name}.mdc",
            "windsurf": "integrations/.windsurf/rules/{name}.md",
            "github": "integrations/.github/instructions/{name}.instructions.md",
        }

        for adapter, pattern in adapters.items():
            for name in ("sage-grill", "sage-wayfinder"):
                path = ROOT / pattern.format(name=name)
                with self.subTest(adapter=adapter, name=name):
                    self.assertTrue(path.is_file(), path)
                    self.assertIn(
                        f"agents/sage/commands/{name}.md",
                        path.read_text(encoding="utf-8"),
                    )

        gemini = read("integrations/gemini.md")
        self.assertIn("sage-grill", gemini)
        self.assertIn("sage-wayfinder", gemini)

    def test_legacy_decision_map_path_is_removed(self) -> None:
        protocol = "\n".join(
            (
                read("AGENTS.md"),
                read("agents/sage/commands/sage.md"),
                read("agents/sage/commands/sage-grill.md"),
                read("agents/sage/commands/sage-flow.md"),
            )
        )

        self.assertNotIn("via `TodoWrite`", protocol)
        self.assertNotIn("`/sage-flow`'s decision-map mode", protocol)


if __name__ == "__main__":
    unittest.main()
