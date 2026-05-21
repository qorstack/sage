"""
Knowlyx MCP Server — exposes cognitive tools to AI agents.

AI agents (Claude Code, Cursor, Codex, etc.) must call these tools
BEFORE generating or modifying code. This is the enforcement layer.

Run:
    knowlyx mcp          # stdio mode (for Claude Code)
    knowlyx mcp --sse    # SSE mode (for HTTP clients)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from knowlyx.graph.cognitive_graph import CognitiveGraph
from knowlyx.reasoning.engine import ReasoningEngine
from knowlyx.scanner.repo_scanner import RepoScanner

mcp = FastMCP(
    name="knowlyx",
    instructions=(
        "Knowlyx is a cognitive enforcement layer. "
        "ALWAYS call analyze_intent FIRST before writing any code. "
        "Then call get_conventions and get_reusable_assets to avoid duplicating existing work. "
        "Never skip these tools — they exist to enforce architectural integrity."
    ),
)

# Module-level state: scan + graph are built once per session
_state: dict[str, Any] = {}


def _get_engine(repo_path: str) -> tuple[ReasoningEngine, RepoScanner]:
    key = str(Path(repo_path).resolve())
    if key not in _state:
        scanner = RepoScanner(repo_path)
        scan = scanner.scan()
        graph = CognitiveGraph()
        graph.build(scan)
        engine = ReasoningEngine(scan, graph)
        _state[key] = (engine, scanner, scan, graph)
    engine, scanner, scan, graph = _state[key]
    return engine, scanner, scan, graph


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------


@mcp.tool()
def analyze_intent(request: str, repo_path: str = ".") -> str:
    """
    REQUIRED FIRST STEP. Analyze the user's request and return a full
    cognitive report: detected intent, inferred requirements, affected
    domains, cascade impact, risk level, and AI decision
    (proceed / warn / ask / reject).

    Call this before ANY code generation or file modification.
    """
    engine, _, scan, _ = _get_engine(repo_path)
    report = engine.analyze(request)

    output: dict[str, Any] = {
        "intent": {
            "domain": report.intent.detected_domain,
            "action": report.intent.detected_action,
            "affected_areas": report.intent.affected_areas,
            "inferred_requirements": report.intent.inferred_requirements,
            "requires_clarification": report.intent.requires_clarification,
            "clarification_questions": report.intent.clarification_questions,
        },
        "impact": {
            "affected_domains": report.impact.affected_domains,
            "affected_services": report.impact.affected_services,
            "cascade_risks": report.impact.cascade_risks,
            "affected_files": [
                {"name": t.name, "path": t.path, "type": t.impact_type, "reason": t.reason}
                for t in report.impact.affected_files
            ],
        },
        "risk": {
            "level": report.risk.level.value,
            "decision": report.risk.decision.value,
            "reasons": report.risk.reasons,
            "warnings": report.risk.warnings,
            "required_workflow": report.risk.required_workflow,
        },
        "suggested_plan": report.suggested_plan,
        "architecture": scan.architecture.value,
        "language": scan.language,
        "framework": scan.framework,
    }

    if report.risk.decision.value == "reject":
        output["HALT"] = (
            "Risk level is CRITICAL. Do NOT proceed without explicit human approval. "
            "Address the warnings above before continuing."
        )
    elif report.risk.decision.value == "ask":
        output["PAUSE"] = "Risk level is HIGH. Ask the user to confirm before proceeding."
    elif report.risk.decision.value == "warn":
        output["NOTICE"] = "Risk level is MEDIUM. Proceed with caution and follow the required workflow."

    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool()
def get_conventions(repo_path: str = ".") -> str:
    """
    Return all detected conventions for this repository.
    These are rules AI MUST follow when generating code.
    Violating them causes architecture drift and review cost.
    """
    _, _, scan, _ = _get_engine(repo_path)
    return json.dumps(
        {
            "architecture": scan.architecture.value,
            "language": scan.language,
            "framework": scan.framework,
            "conventions": [
                {
                    "name": c.name,
                    "rule": c.rule,
                    "enforced": c.enforced,
                    "examples": c.examples,
                }
                for c in scan.conventions
            ],
            "forbidden_patterns": scan.forbidden_patterns,
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def get_reusable_assets(domain: str = "", repo_path: str = ".") -> str:
    """
    Return existing reusable assets (components, hooks, utils, services).
    Check this BEFORE creating new files — reuse what already exists.
    Filter by domain (e.g. 'payment', 'auth', 'user') or leave empty for all.
    """
    _, _, scan, graph = _get_engine(repo_path)
    if domain:
        raw = graph.get_assets_for_domain(domain) + graph.find_reusable(domain)
        seen: set[str] = set()
        assets = []
        for r in raw:
            if r["id"] not in seen:
                seen.add(r["id"])
                assets.append(r)
    else:
        assets = [
            {"id": f"{a.asset_type}:{a.name}", "name": a.name, "type": a.asset_type, "path": a.path, "tags": a.tags}
            for a in scan.reusable_assets
        ]

    return json.dumps(
        {
            "domain_filter": domain or "all",
            "count": len(assets),
            "assets": assets,
            "instruction": "Reuse these before creating new components, hooks, or utils.",
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def get_impact_analysis(change_description: str, repo_path: str = ".") -> str:
    """
    Given a description of a planned change, return the full impact map:
    which domains, services, and files will be affected.
    Use this to understand the blast radius before touching code.
    """
    engine, _, _, _ = _get_engine(repo_path)
    from knowlyx.reasoning.intent_analyzer import IntentAnalyzer
    from knowlyx.reasoning.impact_analyzer import ImpactAnalyzer

    _, _, scan, graph = _get_engine(repo_path)
    intent = IntentAnalyzer(scan).analyze(change_description)
    impact = ImpactAnalyzer(scan, graph).analyze(intent)

    return json.dumps(
        {
            "primary_domain": intent.detected_domain,
            "affected_domains": impact.affected_domains,
            "affected_services": impact.affected_services,
            "cascade_risks": impact.cascade_risks,
            "affected_files": [
                {"name": t.name, "path": t.path, "type": t.impact_type, "reason": t.reason}
                for t in impact.affected_files
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def get_risk_analysis(request: str, repo_path: str = ".") -> str:
    """
    Score the risk of a request and return a decision:
    - proceed: safe to implement
    - warn: proceed with caution, follow the workflow
    - ask: pause and confirm with the user before continuing
    - reject: do NOT proceed without explicit human approval

    Always respect the decision. Never bypass a 'reject'.
    """
    _, _, scan, graph = _get_engine(repo_path)
    from knowlyx.reasoning.intent_analyzer import IntentAnalyzer
    from knowlyx.reasoning.impact_analyzer import ImpactAnalyzer
    from knowlyx.reasoning.risk_scorer import RiskScorer

    intent = IntentAnalyzer(scan).analyze(request)
    impact = ImpactAnalyzer(scan, graph).analyze(intent)
    risk = RiskScorer(scan).score(intent, impact)

    return json.dumps(
        {
            "decision": risk.decision.value,
            "risk_level": risk.level.value,
            "reasons": risk.reasons,
            "warnings": risk.warnings,
            "required_workflow": risk.required_workflow,
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def get_project_context(repo_path: str = ".") -> str:
    """
    Return a lightweight system overview: stack, architecture, domains,
    API clients, and graph statistics.
    Load this at the start of a session to orient yourself.
    """
    _, _, scan, graph = _get_engine(repo_path)
    return json.dumps(
        {
            "language": scan.language,
            "framework": scan.framework,
            "architecture": scan.architecture.value,
            "domains": scan.domains,
            "api_clients": scan.api_clients,
            "has_docker": scan.metadata.get("has_docker", False),
            "has_ci": scan.metadata.get("has_ci", False),
            "is_monorepo": scan.metadata.get("monorepo", False),
            "total_files": scan.metadata.get("total_files", 0),
            "cognitive_graph": graph.summary(),
            "reusable_asset_count": len(scan.reusable_assets),
            "convention_count": len(scan.conventions),
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def refresh_scan(repo_path: str = ".") -> str:
    """
    Force a fresh scan of the repository, discarding cached state.
    Use after significant structural changes to the codebase.
    """
    key = str(Path(repo_path).resolve())
    _state.pop(key, None)
    _, _, scan, graph = _get_engine(repo_path)
    return json.dumps(
        {"status": "refreshed", "domains": scan.domains, "graph": graph.summary()},
        indent=2,
        ensure_ascii=False,
    )
