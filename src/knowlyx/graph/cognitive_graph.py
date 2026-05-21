"""
Cognitive Graph — builds a semantic relationship graph from a ScanResult.

Nodes:  domain | file | service | component | hook | util | convention
Edges:  depends_on | impacts | belongs_to | enforced_by | reuses
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx

from knowlyx.models.schema import ScanResult


class CognitiveGraph:
    def __init__(self) -> None:
        self.g: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, scan: ScanResult) -> None:
        self._add_domains(scan)
        self._add_assets(scan)
        self._add_conventions(scan)
        self._add_impact_edges(scan)

    def _add_domains(self, scan: ScanResult) -> None:
        for domain in scan.domains:
            self.g.add_node(f"domain:{domain}", kind="domain", name=domain)

    def _add_assets(self, scan: ScanResult) -> None:
        for asset in scan.reusable_assets:
            nid = f"{asset.asset_type}:{asset.name}"
            self.g.add_node(nid, kind=asset.asset_type, name=asset.name, path=asset.path, tags=asset.tags)
            for tag in asset.tags:
                if f"domain:{tag}" in self.g:
                    self.g.add_edge(nid, f"domain:{tag}", rel="belongs_to")

    def _add_conventions(self, scan: ScanResult) -> None:
        for conv in scan.conventions:
            nid = f"convention:{conv.name}"
            self.g.add_node(nid, kind="convention", name=conv.name, rule=conv.rule, enforced=conv.enforced)

    def _add_impact_edges(self, scan: ScanResult) -> None:
        # Domain → domain cascades based on known relationships
        _KNOWN_CASCADES: dict[str, list[str]] = {
            "payment": ["webhook", "audit", "notification", "order"],
            "auth": ["user", "notification", "audit"],
            "order": ["payment", "inventory", "notification", "shipping"],
            "user": ["auth", "notification", "audit"],
            "notification": ["user"],
            "webhook": ["payment", "order"],
        }
        for src, targets in _KNOWN_CASCADES.items():
            if f"domain:{src}" in self.g:
                for tgt in targets:
                    if f"domain:{tgt}" in self.g:
                        self.g.add_edge(f"domain:{src}", f"domain:{tgt}", rel="impacts")

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_impact_domains(self, domain: str) -> list[str]:
        """Return domains that are transitively impacted when `domain` changes."""
        nid = f"domain:{domain}"
        if nid not in self.g:
            return []
        reachable = nx.descendants(self.g, nid)
        return [n.split(":", 1)[1] for n in reachable if n.startswith("domain:")]

    def get_assets_for_domain(self, domain: str) -> list[dict[str, Any]]:
        """Return reusable assets tagged to a domain."""
        results: list[dict[str, Any]] = []
        for node, data in self.g.nodes(data=True):
            tags = data.get("tags", [])
            if domain in tags:
                results.append({"id": node, **data})
        return results

    def get_conventions_for_path(self, path: str) -> list[dict[str, Any]]:
        """Return applicable conventions (all enforced ones for now)."""
        return [
            {"id": n, **d}
            for n, d in self.g.nodes(data=True)
            if d.get("kind") == "convention" and d.get("enforced", False)
        ]

    def find_reusable(self, keyword: str) -> list[dict[str, Any]]:
        """Fuzzy search reusable assets by keyword."""
        kw = keyword.lower()
        results: list[dict[str, Any]] = []
        for node, data in self.g.nodes(data=True):
            if data.get("kind") in ("component", "hook", "util", "service"):
                if kw in data.get("name", "").lower() or kw in " ".join(data.get("tags", [])):
                    results.append({"id": node, **data})
        return results

    def node_count(self) -> int:
        return self.g.number_of_nodes()

    def edge_count(self) -> int:
        return self.g.number_of_edges()

    def summary(self) -> dict[str, Any]:
        kinds: dict[str, int] = {}
        for _, data in self.g.nodes(data=True):
            k = data.get("kind", "unknown")
            kinds[k] = kinds.get(k, 0) + 1
        return {"nodes": self.node_count(), "edges": self.edge_count(), "by_kind": kinds}
