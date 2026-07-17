from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class RiskProtocolContractTests(unittest.TestCase):
    def test_canonical_policy_has_operational_risk_lifecycle(self) -> None:
        agents = read("AGENTS.md")

        required_contract = (
            "Impact",
            "Likelihood",
            "Reversibility",
            "Exposure",
            "Confidence",
            "Required controls come from drivers",
            "residual risk",
        )
        for marker in required_contract:
            with self.subTest(marker=marker):
                self.assertIn(marker, agents)

    def test_auto_mode_cannot_approve_high_risk(self) -> None:
        agents = read("AGENTS.md")
        sage = read("agents/sage/commands/sage.md")

        self.assertIn("mode:auto` skips only", agents)
        self.assertIn("HIGH always uses `ask` before file changes", sage)
        self.assertNotIn(
            "risk is HIGH and the user has not approved autonomous execution",
            sage,
        )

    def test_driver_controls_cover_core_failure_classes(self) -> None:
        agents = read("AGENTS.md")

        for driver in (
            "destructive / data loss",
            "schema / data migration",
            "auth / authorization",
            "money / payment",
            "PII / secrets",
            "public contract",
            "production infrastructure",
            "concurrency / external side effect",
            "dependency / supply chain",
            "validation gap / important unknown",
        ):
            with self.subTest(driver=driver):
                self.assertIn(driver, agents)

    def test_specialists_return_control_evidence_and_residual_risk(self) -> None:
        specialists = (
            "agents/sage/commands/sage-flow.md",
            "agents/sage/commands/sage-unit-test.md",
            "agents/sage/commands/sage-e2e-test.md",
            "agents/sage/commands/sage-security-review.md",
        )

        for path in specialists:
            content = read(path)
            with self.subTest(path=path):
                self.assertIn("control", content.lower())
                self.assertIn("evidence", content.lower())
                self.assertIn("Residual", content)

    def test_summary_contract_reports_initial_and_residual_risk(self) -> None:
        agents = read("AGENTS.md")

        self.assertGreaterEqual(agents.count("**Initial risk**"), 2)
        self.assertGreaterEqual(agents.count("**Residual risk**"), 2)


if __name__ == "__main__":
    unittest.main()
