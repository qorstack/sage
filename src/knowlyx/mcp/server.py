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
from knowlyx.memory.schema import MemoryEntry, MemoryKind
from knowlyx.memory.store import create_store
from knowlyx.packs.builtin import get_pack, get_packs_for_domains
from knowlyx.reasoning.engine import ReasoningEngine
from knowlyx.scanner.repo_scanner import RepoScanner

mcp = FastMCP(
    name="knowlyx",
    instructions=(
        "Knowlyx is a cognitive enforcement layer. "
        "ALWAYS call analyze_intent FIRST before writing any code. "
        "Then call get_conventions and get_reusable_assets to avoid duplicating existing work. "
        "Use recall_context to check for human-approved business knowledge before making assumptions. "
        "Never skip these tools — they exist to enforce architectural integrity."
    ),
)

_state: dict[str, Any] = {}


def _get_engine(repo_path: str) -> tuple[ReasoningEngine, Any, CognitiveGraph]:
    key = str(Path(repo_path).resolve())
    if key not in _state:
        scanner = RepoScanner(repo_path)
        scan = scanner.scan()
        graph = CognitiveGraph()
        graph.build(scan)
        engine = ReasoningEngine(scan, graph)
        store = create_store(repo_path)
        _state[key] = (engine, scan, graph, store)
    engine, scan, graph, store = _state[key]
    return engine, scan, graph, store


def _get_store(repo_path: str):
    _, _, _, store = _get_engine(repo_path)
    return store


# ==================================================================
# Phase 1 Tools — Cognitive analysis
# ==================================================================


@mcp.tool()
def analyze_intent(request: str, repo_path: str = ".") -> str:
    """
    REQUIRED FIRST STEP. Analyze the user's request and return a full
    cognitive report: detected intent, inferred requirements, affected
    domains, cascade impact, risk level, AI decision, cognition packs,
    and relevant memory.

    Call this before ANY code generation or file modification.
    """
    engine, scan, _, store = _get_engine(repo_path)
    report = engine.analyze(request)

    # pull cognition packs for affected domains
    all_domains = [report.intent.detected_domain] + report.impact.affected_domains
    packs = get_packs_for_domains(all_domains)

    # pull relevant memory
    memories = store.search(request, limit=5)

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
        "cognition_packs": [
            {
                "domain": p.domain,
                "business_rules": p.business_rules,
                "common_requirements": p.common_requirements,
                "risk_flags": p.risk_flags,
                "required_workflow": p.required_workflow,
                "forbidden_shortcuts": p.forbidden_shortcuts,
                "questions_to_ask": p.questions_to_ask,
            }
            for p in packs
        ],
        "relevant_memory": [
            {"kind": m.kind.value, "title": m.title, "body": m.body, "approved": m.approved}
            for m in memories
            if m.approved  # only surface human-approved memories
        ],
        "suggested_plan": report.suggested_plan,
        "architecture": scan.architecture.value,
        "language": scan.language,
        "framework": scan.framework,
    }

    # persist cognition stamp for commit-check
    try:
        stamp_dir = Path(repo_path) / ".knowlyx"
        stamp_dir.mkdir(parents=True, exist_ok=True)
        stamp = {
            "request": request,
            "decision": report.risk.decision.value,
            "risk_level": report.risk.level.value,
            "domain": report.intent.detected_domain,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
        (stamp_dir / "last_cognition.json").write_text(
            json.dumps(stamp, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass  # don't fail the tool if we can't persist

    decision = report.risk.decision.value
    if decision == "reject":
        output["HALT"] = (
            "Risk level is CRITICAL. Do NOT proceed without explicit human approval. "
            "Address all warnings above before continuing."
        )
    elif decision == "ask":
        output["PAUSE"] = "Risk level is HIGH. Ask the user to confirm before proceeding."
    elif decision == "warn":
        output["NOTICE"] = "Risk level is MEDIUM. Proceed with caution and follow the required workflow."

    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool()
def get_conventions(repo_path: str = ".") -> str:
    """
    Return all detected conventions for this repository.
    These are rules AI MUST follow when generating code.
    Violating them causes architecture drift and review cost.
    """
    _, scan, _, _ = _get_engine(repo_path)
    return json.dumps(
        {
            "architecture": scan.architecture.value,
            "language": scan.language,
            "framework": scan.framework,
            "conventions": [
                {"name": c.name, "rule": c.rule, "enforced": c.enforced, "examples": c.examples}
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
    _, scan, graph, _ = _get_engine(repo_path)
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
    """
    from knowlyx.reasoning.impact_analyzer import ImpactAnalyzer
    from knowlyx.reasoning.intent_analyzer import IntentAnalyzer

    _, scan, graph, _ = _get_engine(repo_path)
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
    proceed / warn / ask / reject.
    Always respect the decision. Never bypass a 'reject'.
    """
    from knowlyx.reasoning.impact_analyzer import ImpactAnalyzer
    from knowlyx.reasoning.intent_analyzer import IntentAnalyzer
    from knowlyx.reasoning.risk_scorer import RiskScorer

    _, scan, graph, _ = _get_engine(repo_path)
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
    API clients, and graph statistics. Load this at session start.
    """
    _, scan, graph, _ = _get_engine(repo_path)
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
def get_cognition_pack(domain: str) -> str:
    """
    Return the full cognition pack for a domain.
    Packs contain business rules, common requirements, risk flags,
    required workflows, and forbidden shortcuts.

    Available domains: auth, otp, payment, webhook, order, notification, worker
    """
    pack = get_pack(domain)
    if not pack:
        return json.dumps({"error": f"No built-in pack for domain '{domain}'. Available: auth, otp, payment, webhook, order, notification, worker"})
    return json.dumps(pack.model_dump(), indent=2, ensure_ascii=False)


@mcp.tool()
def refresh_scan(repo_path: str = ".") -> str:
    """
    Force a fresh scan of the repository, discarding cached state.
    Use after significant structural changes to the codebase.
    """
    key = str(Path(repo_path).resolve())
    _state.pop(key, None)
    _, scan, graph, _ = _get_engine(repo_path)
    return json.dumps(
        {"status": "refreshed", "domains": scan.domains, "graph": graph.summary()},
        indent=2,
        ensure_ascii=False,
    )


# ==================================================================
# Phase 2 Tools — Memory + Human approval
# ==================================================================


@mcp.tool()
def remember_business_context(
    domain: str,
    title: str,
    body: str,
    tags: str = "",
    repo_path: str = ".",
) -> str:
    """
    Save a business context memory for this project.
    Use this to record domain knowledge that isn't obvious from code:
    business rules, product decisions, known constraints, team agreements.

    This memory will surface in future analyze_intent calls.
    Requires human approval via approve_memory before it is trusted.

    Args:
        domain: e.g. 'payment', 'auth', 'order'
        title: short title for this context
        body: full description of the business context
        tags: comma-separated tags (optional)
        repo_path: path to the repository
    """
    store = _get_store(repo_path)
    entry = MemoryEntry(
        id="",
        kind=MemoryKind.BUSINESS_CONTEXT,
        domain=domain,
        title=title,
        body=body,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        approved=False,
        repo_path=repo_path,
    )
    saved = store.save(entry)
    return json.dumps(
        {
            "status": "saved",
            "id": saved.id,
            "approved": False,
            "next_step": f"Call approve_memory('{saved.id}') to mark this as human-approved and trusted.",
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def approve_memory(entry_id: str, approved_by: str = "human", repo_path: str = ".") -> str:
    """
    Human approval step — mark a saved memory as trusted.
    Only approved memories are injected into analyze_intent results.

    This enforces the principle: AI may infer, humans approve.
    """
    store = _get_store(repo_path)
    entry = store.get(entry_id)
    if not entry:
        return json.dumps({"error": f"Memory entry '{entry_id}' not found."})
    entry.approved = True
    entry.approved_by = approved_by
    store.save(entry)
    return json.dumps(
        {"status": "approved", "id": entry_id, "title": entry.title, "approved_by": approved_by},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def recall_context(query: str, domain: str = "", repo_path: str = ".") -> str:
    """
    Fuzzy search memory for relevant business context, team decisions,
    and approved conventions. Use this when you need to know what
    the team has already decided about a topic.

    Only returns human-approved memories.
    """
    store = _get_store(repo_path)
    results = store.search(query, domain=domain, limit=8)
    approved = [r for r in results if r.approved]

    return json.dumps(
        {
            "query": query,
            "domain_filter": domain or "all",
            "count": len(approved),
            "memories": [
                {
                    "id": m.id,
                    "kind": m.kind.value,
                    "domain": m.domain,
                    "title": m.title,
                    "body": m.body,
                    "tags": m.tags,
                    "approved_by": m.approved_by,
                }
                for m in approved
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def remember_team_decision(
    domain: str,
    title: str,
    decision: str,
    reason: str = "",
    repo_path: str = ".",
) -> str:
    """
    Record a team architectural or product decision.
    Examples: 'We use Redis for all caching', 'OTP expires in 5 minutes',
    'Payments are processed async via BullMQ'.

    Decisions are automatically approved (they come from the human caller).
    """
    store = _get_store(repo_path)
    body = decision if not reason else f"{decision}\n\nReason: {reason}"
    entry = MemoryEntry(
        id="",
        kind=MemoryKind.TEAM_DECISION,
        domain=domain,
        title=title,
        body=body,
        approved=True,
        approved_by="team",
        repo_path=repo_path,
    )
    saved = store.save(entry)
    return json.dumps(
        {"status": "saved_and_approved", "id": saved.id, "title": saved.title},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def list_memory(domain: str = "", repo_path: str = ".") -> str:
    """
    List all stored memories, optionally filtered by domain.
    Shows both approved and pending entries.
    """
    store = _get_store(repo_path)
    entries = store.list_by_domain(domain) if domain else store.all()
    return json.dumps(
        {
            "domain_filter": domain or "all",
            "total": len(entries),
            "entries": [
                {
                    "id": e.id,
                    "kind": e.kind.value,
                    "domain": e.domain,
                    "title": e.title,
                    "approved": e.approved,
                    "approved_by": e.approved_by,
                }
                for e in entries
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def forget_memory(entry_id: str, repo_path: str = ".") -> str:
    """Delete a memory entry by ID."""
    store = _get_store(repo_path)
    deleted = store.delete(entry_id)
    return json.dumps({"status": "deleted" if deleted else "not_found", "id": entry_id})


# ==================================================================
# Phase 3 Tools — Workspace + Graph export + Approval queue
# ==================================================================


@mcp.tool()
def get_workspace_context(workspace_path: str = ".") -> str:
    """
    Return the full workspace overview: all repos, their roles,
    cross-repo dependencies, and shared domains.

    Use this when a change may span multiple repositories.
    Requires a knowlyx.toml in workspace_path.
    """
    from knowlyx.workspace.config_loader import load
    from knowlyx.workspace.multi_scanner import WorkspaceScanner

    config = load(workspace_path)
    if not config.repos:
        return json.dumps({
            "warning": "No repos defined in knowlyx.toml. Run `knowlyx workspace init` first.",
            "workspace": config.name,
        })
    scanner = WorkspaceScanner(config)
    ws = scanner.scan()
    return json.dumps(ws.summary(), indent=2, ensure_ascii=False)


@mcp.tool()
def get_cross_repo_impact(changed_repo: str, change_description: str, workspace_path: str = ".") -> str:
    """
    Analyze the cross-repo blast radius of a change to a specific repository.
    Returns which other repos are affected and why.

    Use this before making changes that may cascade across service boundaries.
    """
    from knowlyx.workspace.config_loader import load
    from knowlyx.workspace.multi_scanner import CrossRepoImpactAnalyzer, WorkspaceScanner

    config = load(workspace_path)
    scanner = WorkspaceScanner(config)
    ws = scanner.scan()
    analyzer = CrossRepoImpactAnalyzer(ws, config)
    result = analyzer.analyze(changed_repo, change_description)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def export_graph(
    format: str = "react_flow",
    repo_path: str = ".",
    workspace_path: str = "",
) -> str:
    """
    Export the cognitive graph in the requested format.

    Formats:
      react_flow  — JSON for React Flow component (default)
      mermaid     — Mermaid diagram markdown
      dot         — Graphviz DOT format

    If workspace_path is set, exports the cross-repo workspace graph.
    Otherwise exports the single-repo cognitive graph.
    """
    from knowlyx.graph.exporter import GraphExporter

    if workspace_path:
        from knowlyx.workspace.config_loader import load
        from knowlyx.workspace.multi_scanner import WorkspaceScanner
        config = load(workspace_path)
        ws = WorkspaceScanner(config).scan()
        if format == "mermaid":
            return GraphExporter.workspace_to_mermaid(ws)
        if format == "dot":
            return GraphExporter.workspace_to_dot(ws)
        return json.dumps(GraphExporter.to_workspace_react_flow(ws), indent=2, ensure_ascii=False)

    _, _, graph, _ = _get_engine(repo_path)
    if format == "mermaid":
        return GraphExporter.to_mermaid(graph)
    if format == "dot":
        return GraphExporter.to_dot(graph)
    return json.dumps(GraphExporter.to_react_flow(graph), indent=2, ensure_ascii=False)


@mcp.tool()
def request_approval(
    title: str,
    description: str,
    risk_level: str,
    domain: str,
    requested_action: str,
    impact_summary: str = "",
    warnings: str = "",
    repo_path: str = ".",
) -> str:
    """
    Submit a human approval request before proceeding with a HIGH or CRITICAL risk action.

    AI MUST call this and wait for approval before continuing when:
    - risk decision is 'ask' or 'reject'
    - The change affects critical repos or production systems

    Returns an approval request ID. Poll check_approval(id) to get the outcome.
    Humans approve via `knowlyx approval approve <id>` CLI or approve_request() tool.
    """
    from knowlyx.approval.queue import ApprovalRequest, get_queue

    queue = get_queue(repo_path)
    req = queue.submit(ApprovalRequest(
        title=title,
        description=description,
        risk_level=risk_level,
        domain=domain,
        repo_path=repo_path,
        requested_action=requested_action,
        impact_summary=[s.strip() for s in impact_summary.split(",") if s.strip()],
        warnings=[w.strip() for w in warnings.split(",") if w.strip()],
    ))
    return json.dumps({
        "status": "pending",
        "id": req.id,
        "message": f"Approval request submitted. Human must review before you proceed.",
        "check_with": f"check_approval('{req.id}')",
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def check_approval(request_id: str, repo_path: str = ".") -> str:
    """
    Check the status of a previously submitted approval request.
    Returns: pending | approved | rejected

    If rejected, do NOT proceed. Ask the human how to adjust the approach.
    """
    from knowlyx.approval.queue import get_queue

    queue = get_queue(repo_path)
    req = queue.get(request_id)
    if not req:
        return json.dumps({"error": f"Approval request '{request_id}' not found."})
    return json.dumps({
        "id": req.id,
        "status": req.status.value,
        "title": req.title,
        "reviewed_by": req.reviewed_by,
        "rejection_reason": req.rejection_reason,
        "instruction": {
            "pending": "Do NOT proceed. Wait for human review.",
            "approved": "Approved. You may proceed.",
            "rejected": f"Rejected. Do NOT proceed. Reason: {req.rejection_reason or 'none given'}. Ask the human how to adjust.",
        }.get(req.status.value, "Unknown status"),
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def approve_request(request_id: str, approved_by: str = "human", repo_path: str = ".") -> str:
    """Human-facing tool: approve a pending approval request."""
    from knowlyx.approval.queue import get_queue
    queue = get_queue(repo_path)
    req = queue.approve(request_id, approved_by)
    if not req:
        return json.dumps({"error": f"Request '{request_id}' not found."})
    return json.dumps({"status": "approved", "id": req.id, "title": req.title, "approved_by": req.reviewed_by}, indent=2)


@mcp.tool()
def reject_request(request_id: str, reason: str = "", reviewed_by: str = "human", repo_path: str = ".") -> str:
    """Human-facing tool: reject a pending approval request with a reason."""
    from knowlyx.approval.queue import get_queue
    queue = get_queue(repo_path)
    req = queue.reject(request_id, reason, reviewed_by)
    if not req:
        return json.dumps({"error": f"Request '{request_id}' not found."})
    return json.dumps({"status": "rejected", "id": req.id, "reason": reason}, indent=2)


@mcp.tool()
def validate_generated_code(code: str, repo_path: str = ".", language: str = "") -> str:
    """
    AI self-review: call this BEFORE writing/editing any code file.

    Returns violations + suggestions detected against repo conventions:
    - Hallucinated imports (paths that don't exist)
    - Duplicate of existing reusable assets (reuse instead of recreate)
    - Forbidden patterns from project conventions
    - Hardcoded secrets (Stripe, AWS, GitHub, passwords)
    - Convention violations

    If `has_blockers` is true, DO NOT write the code. Fix the violations
    in-memory and call validate_generated_code again.
    """
    from knowlyx.validation.code_validator import CodeValidator

    _, scan, _, _ = _get_engine(repo_path)
    validator = CodeValidator(scan)
    report = validator.validate(code, language=language or scan.language)
    out = report.to_dict()
    out["instruction"] = (
        "Fix all 'block' severity violations before writing. "
        "Re-call validate_generated_code to verify."
        if report.has_blockers else
        "Validation passed. You may write the code."
    )
    return json.dumps(out, indent=2, ensure_ascii=False)


@mcp.tool()
def list_approvals(status_filter: str = "pending", repo_path: str = ".") -> str:
    """
    List approval requests, filtered by status.
    status_filter: pending | approved | rejected | all
    """
    from knowlyx.approval.queue import ApprovalStatus, get_queue
    queue = get_queue(repo_path)
    if status_filter == "all":
        entries = queue.all()
    elif status_filter == "pending":
        entries = queue.pending()
    else:
        entries = [r for r in queue.all() if r.status.value == status_filter]
    return json.dumps({
        "filter": status_filter,
        "count": len(entries),
        "requests": [
            {
                "id": r.id,
                "title": r.title,
                "domain": r.domain,
                "risk_level": r.risk_level,
                "status": r.status.value,
                "reviewed_by": r.reviewed_by,
                "rejection_reason": r.rejection_reason,
            }
            for r in entries
        ],
    }, indent=2, ensure_ascii=False)
