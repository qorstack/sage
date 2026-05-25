"""Determines what files, services, and domains are impacted by a change."""

from __future__ import annotations

from pathlib import Path

from knowai.graph.cognitive_graph import CognitiveGraph
from knowai.models.schema import ImpactAnalysis, ImpactTarget, IntentAnalysis, ScanResult

_DOMAIN_IMPACT_MAP: dict[str, list[tuple[str, str]]] = {
    "payment": [
        ("webhook", "Payment status changes trigger webhook retries"),
        ("worker", "Async payment processing runs in background workers"),
        ("audit", "Every payment event must be audit logged"),
        ("notification", "Payment success/failure triggers user notification"),
        ("order", "Payment outcome updates order status"),
    ],
    "auth": [
        ("user", "Auth state is tied to user entity"),
        ("notification", "Login alerts may be sent to user"),
        ("audit", "Auth events must be audit logged"),
    ],
    "order": [
        ("payment", "Order creation initiates payment flow"),
        ("inventory", "Order affects stock levels"),
        ("notification", "Order status changes notify user"),
        ("shipping", "Confirmed orders trigger shipping flow"),
        ("audit", "Order lifecycle must be audit logged"),
    ],
    "user": [
        ("auth", "User changes may affect auth state"),
        ("notification", "Profile changes may trigger notifications"),
    ],
    "webhook": [
        ("worker", "Webhook events are processed via job queue"),
        ("audit", "Webhook events are audit logged"),
    ],
}


class ImpactAnalyzer:
    def __init__(self, scan: ScanResult, graph: CognitiveGraph) -> None:
        self.scan = scan
        self.graph = graph

    def analyze(self, intent: IntentAnalysis) -> ImpactAnalysis:
        domain = intent.detected_domain
        affected_domains = self._get_affected_domains(domain, intent.affected_areas)
        affected_files = self._get_affected_files(domain, affected_domains)
        affected_services = self._get_affected_services(affected_domains)
        cascade_risks = self._get_cascade_risks(domain, affected_domains)

        return ImpactAnalysis(
            request=intent.raw_request,
            affected_files=affected_files,
            affected_domains=affected_domains,
            affected_services=affected_services,
            cascade_risks=cascade_risks,
        )

    def _get_affected_domains(self, primary: str, already_detected: list[str]) -> list[str]:
        domains: list[str] = list(dict.fromkeys(already_detected))
        # add graph-based cascade
        graph_impacts = self.graph.get_impact_domains(primary)
        for d in graph_impacts:
            if d not in domains:
                domains.append(d)
        # add rule-based cascade
        for src, targets in _DOMAIN_IMPACT_MAP.items():
            if src == primary or src in domains:
                for tgt, _ in targets:
                    if tgt not in domains:
                        domains.append(tgt)
        return domains

    def _get_affected_files(self, primary: str, affected_domains: list[str]) -> list[ImpactTarget]:
        targets: list[ImpactTarget] = []
        seen: set[str] = set()

        def add(path: str, impact_type: str, reason: str, name: str = "") -> None:
            if path not in seen:
                seen.add(path)
                targets.append(ImpactTarget(name=name or Path(path).name, path=path, impact_type=impact_type, reason=reason))

        # scan for files matching domain keywords
        for domain in [primary] + affected_domains:
            for asset in self.scan.reusable_assets:
                if domain in asset.tags or domain in asset.name.lower():
                    add(asset.path, "direct", f"Asset tagged to domain '{domain}'", asset.name)

        # flag generated API client if it exists
        for client_path in self.scan.api_clients:
            add(client_path, "indirect", "Generated API client may need regeneration after DTO changes", "api-client")

        return targets

    def _get_affected_services(self, affected_domains: list[str]) -> list[str]:
        services: list[str] = []
        _SERVICE_MAP = {
            "payment": "payment-service",
            "auth": "auth-service",
            "order": "order-service",
            "notification": "notification-service",
            "webhook": "webhook-service",
            "worker": "worker / job-queue",
            "audit": "audit-service",
            "inventory": "inventory-service",
            "shipping": "shipping-service",
            "user": "user-service",
            "search": "search-service",
        }
        for domain in affected_domains:
            svc = _SERVICE_MAP.get(domain)
            if svc and svc not in services:
                services.append(svc)
        return services

    def _get_cascade_risks(self, primary: str, affected_domains: list[str]) -> list[str]:
        risks: list[str] = []
        for src, targets in _DOMAIN_IMPACT_MAP.items():
            if src == primary:
                for tgt, reason in targets:
                    if tgt in affected_domains:
                        risks.append(f"[{src} → {tgt}] {reason}")
        if self.scan.api_clients and primary in ("payment", "auth", "order", "user"):
            risks.append("Backend DTO changes require Swagger regeneration and client rebuild")
        return risks
