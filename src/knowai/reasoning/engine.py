"""High-level reasoning engine — orchestrates intent → impact → risk → report."""

from __future__ import annotations

from knowai.graph.cognitive_graph import CognitiveGraph
from knowai.models.schema import CognitionReport, ScanResult
from knowai.reasoning.impact_analyzer import ImpactAnalyzer
from knowai.reasoning.intent_analyzer import IntentAnalyzer
from knowai.reasoning.risk_scorer import RiskScorer


class ReasoningEngine:
    def __init__(self, scan: ScanResult, graph: CognitiveGraph) -> None:
        self.scan = scan
        self.graph = graph
        self._intent_analyzer = IntentAnalyzer(scan)
        self._impact_analyzer = ImpactAnalyzer(scan, graph)
        self._risk_scorer = RiskScorer(scan)

    def analyze(self, request: str) -> CognitionReport:
        intent = self._intent_analyzer.analyze(request)
        impact = self._impact_analyzer.analyze(intent)
        risk = self._risk_scorer.score(intent, impact)
        conventions = self._relevant_conventions(intent.detected_domain)
        assets = self._relevant_assets(intent.detected_domain)
        plan = self._build_plan(intent, impact, risk)

        return CognitionReport(
            intent=intent,
            impact=impact,
            risk=risk,
            conventions_to_follow=conventions,
            reusable_assets_to_use=assets,
            suggested_plan=plan,
        )

    def _relevant_conventions(self, domain: str):
        from knowai.models.schema import Convention
        return [
            Convention(name=c["name"], rule=c["rule"], enforced=c.get("enforced", False))
            for c in self.graph.get_conventions_for_path("")
        ]

    def _relevant_assets(self, domain: str):
        from knowai.models.schema import ReusableAsset
        raw = self.graph.get_assets_for_domain(domain) + self.graph.find_reusable(domain)
        seen: set[str] = set()
        assets = []
        for r in raw:
            if r["id"] not in seen:
                seen.add(r["id"])
                assets.append(ReusableAsset(
                    name=r.get("name", ""),
                    asset_type=r.get("kind", "util"),
                    path=r.get("path", ""),
                    tags=r.get("tags", []),
                ))
        return assets

    def _build_plan(self, intent, impact, risk) -> list[str]:
        plan: list[str] = []
        step = 1

        if risk.required_workflow:
            return risk.required_workflow

        if intent.detected_action == "add":
            plan.append(f"{step}. Check reusable assets before creating new code")
            step += 1
        if impact.affected_domains:
            plan.append(f"{step}. Understand impact on: {', '.join(impact.affected_domains[:4])}")
            step += 1
        plan.append(f"{step}. Follow conventions for '{self.scan.architecture.value}' architecture")
        step += 1
        if self.scan.api_clients:
            plan.append(f"{step}. If DTOs change → regenerate Swagger client")
            step += 1
        plan.append(f"{step}. Write tests covering the affected domains")
        return plan
