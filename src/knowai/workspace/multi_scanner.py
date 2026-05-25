"""
Multi-repo scanner — scans all repos in a workspace and builds
a unified cross-repo cognitive graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

from knowai.graph.cognitive_graph import CognitiveGraph
from knowai.models.schema import ScanResult
from knowai.scanner.repo_scanner import RepoScanner
from knowai.workspace.schema import WorkspaceConfig


@dataclass
class RepoState:
    name: str
    path: str
    role: str
    scan: ScanResult
    graph: CognitiveGraph
    critical: bool = False


@dataclass
class WorkspaceScanResult:
    workspace_name: str
    repos: list[RepoState] = field(default_factory=list)
    cross_repo_graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    errors: dict[str, str] = field(default_factory=dict)

    def get_repo(self, name: str) -> RepoState | None:
        return next((r for r in self.repos if r.name == name), None)

    def all_domains(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for r in self.repos:
            for d in r.scan.domains:
                if d not in seen:
                    seen.add(d)
                    result.append(d)
        return result

    def summary(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace_name,
            "repos": [
                {
                    "name": r.name,
                    "role": r.role,
                    "language": r.scan.language,
                    "framework": r.scan.framework,
                    "architecture": r.scan.architecture.value,
                    "domains": r.scan.domains,
                    "critical": r.critical,
                    "files": r.scan.metadata.get("total_files", 0),
                }
                for r in self.repos
            ],
            "cross_repo_edges": self.cross_repo_graph.number_of_edges(),
            "all_domains": self.all_domains(),
            "errors": self.errors,
        }


class WorkspaceScanner:
    def __init__(self, config: WorkspaceConfig, persist_cache: bool = False) -> None:
        self.config = config
        self.persist_cache = persist_cache

    def scan(self) -> WorkspaceScanResult:
        from knowai.cache.scan_cache import ScanCache

        result = WorkspaceScanResult(workspace_name=self.config.name)
        cache = ScanCache(self.config.name)

        # 1. scan each repo — use cache when repo isn't physically present
        for repo_cfg in self.config.repos:
            path = Path(repo_cfg.path)
            scan: ScanResult | None = None
            source = "fresh"

            if path.exists():
                try:
                    scanner = RepoScanner(path)
                    scan = scanner.scan()
                    if self.persist_cache:
                        cache.save(repo_cfg.name, scan)
                except Exception as e:
                    # fresh scan failed — try cache as fallback
                    cached = cache.load(repo_cfg.name)
                    if cached:
                        scan = cached
                        source = "cache (fresh scan failed)"
                        result.errors[repo_cfg.name] = f"used cache; fresh scan error: {e}"
                    else:
                        result.errors[repo_cfg.name] = str(e)
                        continue
            else:
                # repo not on disk — try cache
                cached = cache.load(repo_cfg.name)
                if cached:
                    scan = cached
                    source = "cache (repo not on disk)"
                else:
                    result.errors[repo_cfg.name] = (
                        f"Path not found and no cached scan: {repo_cfg.path}. "
                        f"Clone the repo or run `knowai workspace scan --persist` "
                        f"on a machine that has it."
                    )
                    continue

            # inject declared domains if scanner missed them
            for d in repo_cfg.domains:
                if d not in scan.domains:
                    scan.domains.append(d)
            graph = CognitiveGraph()
            graph.build(scan)
            scan.metadata.setdefault("scan_source", source)
            result.repos.append(RepoState(
                name=repo_cfg.name,
                path=str(path),
                role=repo_cfg.role.value,
                scan=scan,
                graph=graph,
                critical=repo_cfg.critical,
            ))

        # 2. build cross-repo graph
        result.cross_repo_graph = self._build_cross_repo_graph(result)
        return result

    def _build_cross_repo_graph(self, ws: WorkspaceScanResult) -> nx.DiGraph:
        g = nx.DiGraph()

        # add repo nodes
        for repo in ws.repos:
            g.add_node(
                repo.name,
                kind="repo",
                role=repo.role,
                language=repo.scan.language,
                framework=repo.scan.framework,
                domains=repo.scan.domains,
                critical=repo.critical,
            )

        # declared dependencies from config
        for dep in self.config.dependencies:
            if g.has_node(dep.from_repo) and g.has_node(dep.to_repo):
                g.add_edge(dep.from_repo, dep.to_repo, rel=dep.dependency_type, description=dep.description)

        # inferred: frontend → backend if frontend has API clients
        for repo in ws.repos:
            if repo.scan.api_clients:
                # this repo consumes a generated API — find who it might come from
                for other in ws.repos:
                    if other.name != repo.name and other.role in ("backend", "gateway"):
                        if not g.has_edge(repo.name, other.name):
                            g.add_edge(repo.name, other.name, rel="api_inferred", description="Generated API client detected")

        # inferred: worker repos listen to payment/webhook domains
        for repo in ws.repos:
            if repo.role == "worker":
                for other in ws.repos:
                    if other.name != repo.name:
                        shared = set(repo.scan.domains) & set(other.scan.domains)
                        if shared:
                            g.add_edge(other.name, repo.name, rel="event", description=f"Shared domains: {', '.join(shared)}")

        return g


class CrossRepoImpactAnalyzer:
    def __init__(self, ws: WorkspaceScanResult, config: WorkspaceConfig) -> None:
        self.ws = ws
        self.config = config

    def analyze(self, changed_repo: str, change_description: str) -> dict[str, Any]:
        g = self.ws.cross_repo_graph
        if changed_repo not in g:
            return {"error": f"Repo '{changed_repo}' not found in workspace"}

        # repos that depend on changed_repo (transitively)
        dependents = list(nx.ancestors(g, changed_repo)) if g.has_node(changed_repo) else []
        # repos that changed_repo depends on
        dependencies = list(nx.descendants(g, changed_repo)) if g.has_node(changed_repo) else []

        # collect impact per dependent repo
        per_repo_impact: list[dict] = []
        for dep_name in dependents:
            dep = self.ws.get_repo(dep_name)
            edge_data = g.get_edge_data(dep_name, changed_repo) or g.get_edge_data(changed_repo, dep_name) or {}
            per_repo_impact.append({
                "repo": dep_name,
                "role": dep.role if dep else "unknown",
                "relation": edge_data.get("rel", "unknown"),
                "domains": dep.scan.domains if dep else [],
                "critical": dep.critical if dep else False,
                "reason": edge_data.get("description", f"Depends on {changed_repo}"),
            })

        # overall risk: critical repo impacted?
        critical_hit = any(r["critical"] for r in per_repo_impact)

        return {
            "changed_repo": changed_repo,
            "change": change_description,
            "directly_affected_repos": [
                n for n in g.successors(changed_repo)
            ],
            "all_affected_repos": dependents,
            "dependencies_of_changed": dependencies,
            "per_repo_impact": per_repo_impact,
            "critical_repos_affected": critical_hit,
            "recommendation": (
                "STOP — critical repo affected, require human review"
                if critical_hit else
                "Proceed with caution — verify all affected repos"
            ),
        }
