"""
Precept MCP Server — exposes cognitive tools to AI agents.

AI agents (Claude Code, Cursor, Codex, etc.) must call these tools
BEFORE generating or modifying code. This is the enforcement layer.

Run:
    precept mcp          # stdio mode (for Claude Code)
    precept mcp --sse    # SSE mode (for HTTP clients)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from precept import audit
from precept.graph.cognitive_graph import CognitiveGraph
from precept.memory.schema import MemoryEntry, MemoryKind, MemoryScope, MemorySource
from precept.memory.store import create_store
from precept.packs.builtin import get_pack, get_packs_for_domains
from precept.reasoning.engine import ReasoningEngine
from precept.scanner.repo_scanner import RepoScanner
from precept.skills import load_workspace_skills
from precept.skills import read_skill as _read_skill

# ---------------------------------------------------------------------------
# Memory body sanitization
# ---------------------------------------------------------------------------
# Strips Anthropic-style tool-call XML that occasionally leaks into memory
# text when the agent mis-formats nested invoke blocks (observed in real
# entries: `</invoke>`, `<parameter name="reason">…`, `</decision>`).
#
# We intentionally limit the tag list to ones that belong to the tool-call
# protocol (invoke / parameter / decision / reason / tags) so that genuine
# HTML inside a memory body (e.g. `<div>`, `<form>`) is preserved. The stray
# `<body>` case is handled only when it appears next to another known leak
# tag — this catches the `</body>\n</invoke>` pattern without harming
# memory entries that legitimately describe HTML pages.
_TOOL_LEAK_RE = re.compile(
    r"</?\s*(?:invoke|parameter|decision|reason|tags)\b[^>]*>",
    re.IGNORECASE,
)
_STRAY_BODY_RE = re.compile(
    r"</?\s*body\s*>(?=\s*(?:</?\s*(?:invoke|parameter|decision|reason|tags)\b|\Z))",
    re.IGNORECASE,
)


def _sanitize_memory_text(text: str) -> str:
    """Remove leaked tool-call XML fragments before persisting memory text."""
    if not text:
        return text
    cleaned = _TOOL_LEAK_RE.sub("", text)
    cleaned = _STRAY_BODY_RE.sub("", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _apply_supersedes(store, supersedes_id: str, new_id: str) -> dict:
    """Mark `supersedes_id` as superseded by `new_id` if both are valid.

    Returns a small status dict so the caller can include it in the tool
    response. Failures are non-fatal — the new save has already succeeded.
    """
    if not supersedes_id or supersedes_id == new_id:
        return {"status": "noop"}
    if not hasattr(store, "mark_superseded"):
        return {"status": "unsupported"}
    try:
        ok = store.mark_superseded(supersedes_id, new_id)
    except Exception as exc:  # pragma: no cover — defensive, log via audit
        return {"status": "error", "reason": str(exc), "id": supersedes_id}
    return {"status": "ok" if ok else "not_found", "id": supersedes_id, "by": new_id}

mcp = FastMCP(
    name="precept",
    instructions=(
        "Precept is a cognitive enforcement layer. Mandatory workflow for ANY code change:\n"
        "\n"
        "1. analyze_intent(request) — FIRST. Returns rule-based decision + impact + risk +\n"
        "   `available_skills` (team-authored knowledge files: name + description).\n"
        "2. Scan `available_skills`. For every skill whose description sounds relevant to\n"
        "   the task, call read_skill(name) and follow its guidance.\n"
        "3. If decision is 'ask' or 'reject' → call request_approval() and wait.\n"
        "4. get_domain_knowledge(domain) — read related memory. If synthesis is stale,\n"
        "   YOU must distill themes/conflicts/open-questions and call save_synthesis().\n"
        "5. get_reusable_assets(domain) — reuse before creating.\n"
        "6. assess_risk_in_context(request) — you may UPGRADE the rule-based decision\n"
        "   if historical context (memory) warrants it. You may NEVER downgrade it.\n"
        "7. validate_generated_code(code) — BEFORE writing. Fix all blockers, re-validate.\n"
        "\n"
        "Knowledge capture — INVISIBLE TO THE DEV:\n"
        "When the dev states a team rule, convention, style guide, or domain principle\n"
        "during conversation, capture it WITHOUT asking permission:\n"
        " - structured guidance, multi-rule conventions → call save_skill(name, description, body)\n"
        " - single decision with reasoning → call remember_team_decision(domain, title, decision, reason)\n"
        " - inferred context that needs human ratification → call remember_business_context(...)\n"
        "All three auto-sync to the team's git remote on save. The dev never needs to\n"
        "run git or precept CLI commands — you handle persistence and propagation.\n"
        "\n"
        "DIFF BEFORE EVERY WRITE. Before ANY remember_*/save_skill/save_synthesis call,\n"
        "first call recall_context (or list_memory / read_skill) for that domain. Then:\n"
        " - No similar entry → write fresh.\n"
        " - Existing entry, content still matches reality → do nothing.\n"
        " - Existing entry, content is stale → re-call the SAME tool with the SAME title;\n"
        "   the store upserts in place. Don't create a near-duplicate just to reword.\n"
        "Skipping this check produces duplicate, stale memory — the most common failure\n"
        "mode of precept. This rule applies in normal chat, not just /precept-generate.\n"
        "\n"
        "Rule: Precept decisions are AUTHORITATIVE. You may only make them stricter, never looser.\n"
        "Synthesis you save is cached and reused by future sessions — do it carefully.\n"
        "\n"
        "ALWAYS SURFACE RISK TO THE USER. For every coding request — even small ones —\n"
        "after analyze_intent and (when relevant) assess_risk_in_context, include a\n"
        "1-2 line risk header at the top of your reply, in this shape:\n"
        "  Risk: <LOW|MEDIUM|HIGH> — <one-sentence why>\n"
        "  Decision: <proceed|warn|ask|reject>\n"
        "If risk is HIGH or decision is ask/reject, stop and wait for the user before\n"
        "writing code. The user should never have to guess the risk level — show it."
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


def _workspace_name_for(repo_path: str) -> str | None:
    """Resolve the workspace name this repo is linked to. None if not linked."""
    try:
        from precept.link.resolver import resolve_workspace
        res = resolve_workspace(repo_path)
        return res.workspace_name if res else None
    except Exception:
        return None


def _ai_auto_approve(repo_path: str) -> bool:
    """
    Check whether AI-written memory should auto-approve at save time.
    Per-repo precept.config wins over ~/.precept.config (global fallback).
    """
    try:
        from precept.link.config import load_global_link, load_link
        link = load_link(repo_path)
        if link is not None:
            return bool(link.auto_approve_ai_memory)
        glob = load_global_link()
        return bool(glob and glob.get("auto_approve_ai_memory"))
    except Exception:
        return False


def _ai_scope_tag(repo_path: str) -> tuple[MemoryScope, str, str]:
    """
    For AI-written memory: derive (scope, workspace, repo_name) from the repo's
    precept.config (searched up the tree, then ~/.precept.config). If the repo
    isn't linked to any workspace, fall back to global so the entry is still
    visible (Claude shouldn't lose work just because the user forgot to link).
    """
    try:
        from precept.link.resolver import scope_tag
        scope, workspace, repo_name = scope_tag(repo_path)
        return MemoryScope(scope), workspace, repo_name
    except Exception:
        return MemoryScope.GLOBAL, "", ""


# Throttle auto-pull so we don't hammer git on every MCP read. One pull per
# workspace every N seconds is plenty — humans don't write decisions faster.
_PULL_THROTTLE_SECONDS = 10
_last_pull_at: dict[str, float] = {}


def _resolve_ws_dir(repo_path: str):
    """Return the workspace folder for a repo, or None. Used by sync hooks."""
    from pathlib import Path
    try:
        from precept.link.resolver import resolve_workspace
        res = resolve_workspace(repo_path)
        if res is not None:
            return res.workspace_dir
    except Exception:
        pass
    p = Path(repo_path).resolve()
    while True:
        if (p / "workspace.toml").exists():
            return p
        if p.parent == p:
            return None
        p = p.parent


def _auto_pull_workspace(repo_path: str) -> None:
    """Before MCP reads, schedule a background `git pull` so the NEXT read
    sees teammates' latest. Returns instantly — current read uses whatever
    is on disk right now. Throttled to one pull per 10s per workspace."""
    try:
        import threading
        import time

        from precept import sync as _sync
        if not _sync.sync_enabled():
            return
        ws_dir = _resolve_ws_dir(repo_path)
        if ws_dir is None:
            return
        key = str(ws_dir)
        now = time.monotonic()
        if now - _last_pull_at.get(key, 0) < _PULL_THROTTLE_SECONDS:
            return
        _last_pull_at[key] = now
        # Daemon thread is fine here — the MCP server is long-running and
        # the pull will complete in the background, ready for the next call.
        threading.Thread(target=lambda: _sync.pull(ws_dir), daemon=True).start()
    except Exception:
        pass


def _auto_sync_after_write(repo_path: str, message: str) -> None:
    """After MCP writes, schedule a background pull+push. Returns instantly."""
    try:
        from precept import sync as _sync
        if not _sync.sync_enabled():
            return
        ws_dir = _resolve_ws_dir(repo_path)
        if ws_dir is None:
            return
        _sync.schedule_full_sync(ws_dir, message=message)
    except Exception:
        pass


def _available_skills_summary(
    repo_path: str,
    domains: list[str] | None = None,
    max_results: int = 15,
) -> list[dict[str, Any]]:
    """Return [{name, description, tags}] of skills relevant to the current task.

    Filtering keeps the analyze_intent payload small on large projects:

    - If `domains` is provided, only skills whose name/description/tags match
      one of the domain keywords are surfaced.
    - If the filter excludes everything (no match found), we fall back to the
      full list — better to be slightly noisy than hide everything.
    - Result is capped at `max_results` so even an aggressive matcher can't
      explode context size.

    Claude still scans these descriptions and decides which to `read_skill()`.
    """
    ws_name = _workspace_name_for(repo_path)
    if not ws_name:
        return []
    try:
        skills = load_workspace_skills(ws_name)
    except Exception:
        return []
    if not skills:
        return []

    keywords = {d.lower() for d in (domains or []) if d}
    if keywords:
        import re
        # Word-boundary match so e.g. `ui` doesn't accidentally match `built-in`.
        patterns = [re.compile(rf"\b{re.escape(k)}\b") for k in keywords]
        filtered = []
        for s in skills:
            haystack = (s.name + " " + s.description + " " + " ".join(s.tags)).lower()
            if any(p.search(haystack) for p in patterns):
                filtered.append(s)
        chosen = filtered if filtered else skills
    else:
        chosen = skills

    return [
        {"name": s.name, "description": s.description, "tags": s.tags}
        for s in chosen[:max_results]
    ]


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
    _auto_pull_workspace(repo_path)
    engine, scan, _, store = _get_engine(repo_path)
    report = engine.analyze(request)
    audit.log(repo_path, "analyze_intent", request=request, decision=report.risk.decision.value, domain=report.intent.detected_domain)

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
        "available_skills": _available_skills_summary(repo_path, domains=all_domains),
        "suggested_plan": report.suggested_plan,
        "architecture": scan.architecture.value,
        "language": scan.language,
        "framework": scan.framework,
    }

    # persist cognition stamp for commit-check
    try:
        stamp_dir = Path(repo_path) / ".precept"
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

    # Binding rule for AI agents
    output["risk_policy"] = {
        "rule": "Precept decision is authoritative. You may UPGRADE risk based on context "
                "(proceed → warn → ask → reject). You may NEVER downgrade. "
                "If you upgrade to 'ask' or 'reject', call request_approval() before coding.",
        "order": ["proceed", "warn", "ask", "reject"],
        "current": decision,
    }

    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool()
def get_conventions(repo_path: str = ".") -> str:
    """
    Return all detected conventions for this repository.
    These are rules AI MUST follow when generating code.
    Violating them causes architecture drift and review cost.
    """
    audit.log(repo_path, "get_conventions")
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
    audit.log(repo_path, "get_reusable_assets", domain=domain)
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
    from precept.reasoning.impact_analyzer import ImpactAnalyzer
    from precept.reasoning.intent_analyzer import IntentAnalyzer

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
    from precept.reasoning.impact_analyzer import ImpactAnalyzer
    from precept.reasoning.intent_analyzer import IntentAnalyzer
    from precept.reasoning.risk_scorer import RiskScorer

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
    supersedes_id: str = "",
) -> str:
    """
    Save a business context memory for this project.
    Use this to record domain knowledge that isn't obvious from code:
    business rules, product decisions, known constraints, team agreements.

    **Diff before you write.** Always call `recall_context(query=title, domain=domain)`
    or `list_memory(domain=domain)` first, then:

    - No similar entry → create.
    - Same kind+title and body still accurate → DO NOT call this tool; nothing changed.
    - Same kind+title but body is stale → call this tool with the SAME title; the store
      upserts by sha256(kind:domain:title) so the body refreshes in place.
    - Title drifted → update the existing title's body, don't create a near-duplicate.

    This memory will surface in future analyze_intent calls.
    Requires human approval via approve_memory before it is trusted.

    Args:
        domain: e.g. 'payment', 'auth', 'order'
        title: short title for this context
        body: full description of the business context
        tags: comma-separated tags (optional)
        repo_path: path to the repository
        supersedes_id: if this entry replaces an older one whose information
            is now wrong or out of date, pass its id — the old entry will be
            marked superseded (preserved for audit, hidden from recall).
    """
    title = _sanitize_memory_text(title)
    body = _sanitize_memory_text(body)
    tags = _sanitize_memory_text(tags)
    store = _get_store(repo_path)
    scope, workspace, repo_name = _ai_scope_tag(repo_path)
    auto_approve = _ai_auto_approve(repo_path)
    entry = MemoryEntry(
        id="",
        kind=MemoryKind.BUSINESS_CONTEXT,
        domain=domain,
        title=title,
        body=body,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        approved=auto_approve,
        approved_by="ai-auto" if auto_approve else "",
        repo_path=repo_path,
        scope=scope,
        source=MemorySource.AI,
        workspace=workspace,
        repo_name=repo_name,
    )
    saved = store.save(entry)
    superseded = _apply_supersedes(store, supersedes_id, saved.id)
    sync_tag = "auto-approved" if auto_approve else "pending approval"
    _auto_sync_after_write(repo_path, f"memory({domain}): {saved.title[:60]} ({sync_tag})")
    next_step = (
        "Auto-approved (auto_approve_ai_memory=true). Humans can review/edit/delete on the dashboard."
        if auto_approve
        else f"Call approve_memory('{saved.id}') to mark this as human-approved and trusted."
    )
    return json.dumps(
        {
            "status": "saved",
            "id": saved.id,
            "approved": auto_approve,
            "superseded": superseded,
            "next_step": next_step,
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
    _auto_sync_after_write(repo_path, f"memory({entry.domain}): approve {entry_id[:8]}")
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
    _auto_pull_workspace(repo_path)
    audit.log(repo_path, "recall_context", query=query, domain=domain)
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
    supersedes_id: str = "",
) -> str:
    """
    Record a team architectural or product decision.
    Examples: 'We use Redis for all caching', 'OTP expires in 5 minutes',
    'Payments are processed async via BullMQ'.

    **Diff before you write.** Same rule as `remember_business_context`: call
    `recall_context` or `list_memory` first, skip if unchanged, re-call with
    the SAME title to refresh a stale decision, and never create a
    near-duplicate just because the wording drifted.

    Decisions are automatically approved (they come from the human caller).

    Args:
        supersedes_id: if this decision replaces an older one whose conclusion
            is now wrong or has been flipped by the team, pass its id — the old
            entry will be marked superseded (preserved for audit, hidden from
            recall) so future sessions don't see contradictory guidance.
    """
    title = _sanitize_memory_text(title)
    decision = _sanitize_memory_text(decision)
    reason = _sanitize_memory_text(reason)
    store = _get_store(repo_path)
    scope, workspace, repo_name = _ai_scope_tag(repo_path)
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
        scope=scope,
        source=MemorySource.AI,
        workspace=workspace,
        repo_name=repo_name,
    )
    saved = store.save(entry)
    superseded = _apply_supersedes(store, supersedes_id, saved.id)
    _auto_sync_after_write(repo_path, f"memory({domain}): {saved.title[:60]}")
    return json.dumps(
        {
            "status": "saved_and_approved",
            "id": saved.id,
            "title": saved.title,
            "superseded": superseded,
        },
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
    if deleted:
        _auto_sync_after_write(repo_path, f"memory: forget {entry_id[:8]}")
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
    Requires a precept.toml in workspace_path.
    """
    from precept.workspace.config_loader import load
    from precept.workspace.multi_scanner import WorkspaceScanner

    config = load(workspace_path)
    if not config.repos:
        return json.dumps({
            "warning": "No repos defined in precept.toml. Run `precept workspace init` first.",
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
    from precept.workspace.config_loader import load
    from precept.workspace.multi_scanner import CrossRepoImpactAnalyzer, WorkspaceScanner

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
    from precept.graph.exporter import GraphExporter

    if workspace_path:
        from precept.workspace.config_loader import load
        from precept.workspace.multi_scanner import WorkspaceScanner
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
    Humans approve via `precept approval approve <id>` CLI or approve_request() tool.
    """
    from precept.approval.queue import ApprovalRequest, get_queue

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
    audit.log(repo_path, "request_approval", title=title, risk_level=risk_level, domain=domain, request_id=req.id)
    _auto_sync_after_write(repo_path, f"approval: request {req.id[:8]} ({domain})")
    return json.dumps({
        "status": "pending",
        "id": req.id,
        "message": "Approval request submitted. Human must review before you proceed.",
        "check_with": f"check_approval('{req.id}')",
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def check_approval(request_id: str, repo_path: str = ".") -> str:
    """
    Check the status of a previously submitted approval request.
    Returns: pending | approved | rejected

    If rejected, do NOT proceed. Ask the human how to adjust the approach.
    """
    from precept.approval.queue import get_queue

    queue = get_queue(repo_path)
    req = queue.get(request_id)
    if not req:
        audit.log(repo_path, "check_approval", request_id=request_id, status="not_found")
        return json.dumps({"error": f"Approval request '{request_id}' not found."})
    audit.log(repo_path, "check_approval", request_id=request_id, status=req.status.value)
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
    from precept.approval.queue import get_queue
    queue = get_queue(repo_path)
    req = queue.approve(request_id, approved_by)
    if not req:
        return json.dumps({"error": f"Request '{request_id}' not found."})
    return json.dumps({"status": "approved", "id": req.id, "title": req.title, "approved_by": req.reviewed_by}, indent=2)


@mcp.tool()
def reject_request(request_id: str, reason: str = "", reviewed_by: str = "human", repo_path: str = ".") -> str:
    """Human-facing tool: reject a pending approval request with a reason."""
    from precept.approval.queue import get_queue
    queue = get_queue(repo_path)
    req = queue.reject(request_id, reason, reviewed_by)
    if not req:
        return json.dumps({"error": f"Request '{request_id}' not found."})
    return json.dumps({"status": "rejected", "id": req.id, "reason": reason}, indent=2)


@mcp.tool()
def get_domain_knowledge(domain: str, repo_path: str = ".") -> str:
    """
    Return ALL approved memory entries for a domain as raw structured data,
    PLUS a cached synthesis if available and still fresh.

    YOU (the AI agent) MUST do the following BEFORE coding in this domain:
    1. If `synthesis.stale` is true OR `synthesis` is null:
       - Read all entries
       - Identify: (a) common themes, (b) conflicting decisions, (c) open questions
       - Call `save_synthesis(domain, summary, key_themes, open_questions)` to cache
    2. Use the synthesis (yours or cached) to guide the implementation.

    The cached synthesis is reused by all future calls until new entries arrive
    (the system marks it stale automatically).
    """
    _auto_pull_workspace(repo_path)
    _, _, _, store = _get_engine(repo_path)
    entries = [e for e in store.all() if e.domain == domain and e.approved]
    synthesis = store.get_synthesis(domain) if hasattr(store, "get_synthesis") else None
    stale = store.synthesis_stale(domain) if hasattr(store, "synthesis_stale") else True
    audit.log(repo_path, "get_domain_knowledge", domain=domain, entries=len(entries), synthesis_stale=bool(stale))

    return json.dumps({
        "domain": domain,
        "entry_count": len(entries),
        "entries": [
            {
                "id": e.id,
                "kind": e.kind.value,
                "title": e.title,
                "body": e.body,
                "tags": e.tags,
                "approved_by": e.approved_by,
            }
            for e in entries
        ],
        "synthesis": synthesis,
        "synthesis_stale": stale,
        "instruction_for_ai": (
            "Synthesis is stale or missing. Read entries, then call "
            "save_synthesis() with: a 3-5 sentence summary tying related "
            "decisions together, a list of key themes, and open questions."
            if stale else
            "Cached synthesis is fresh. Use it directly."
        ),
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def save_synthesis(
    domain: str,
    summary: str,
    key_themes: list[str],
    open_questions: list[str] = None,
    repo_path: str = ".",
) -> str:
    """
    Cache YOUR synthesis of related memory entries for a domain.

    Call this AFTER reading raw entries from get_domain_knowledge() and
    distilling them into a coherent summary that groups RELATED CONTENT.

    The cached synthesis is reused by all future calls until new memory
    entries arrive in this domain (then it's marked stale automatically).

    Args:
      summary: 3-5 sentence narrative tying related decisions together
      key_themes: ["idempotency", "stripe", "refund-policy"] etc.
      open_questions: things the memory hasn't decided yet
    """
    _, _, _, store = _get_engine(repo_path)
    if not hasattr(store, "save_synthesis"):
        return json.dumps({"error": "store does not support synthesis caching"})
    summary = _sanitize_memory_text(summary)
    key_themes = [_sanitize_memory_text(t) for t in (key_themes or [])]
    open_questions = [_sanitize_memory_text(q) for q in (open_questions or [])]
    saved = store.save_synthesis(
        domain=domain,
        summary=summary,
        key_themes=key_themes,
        open_questions=open_questions,
        synthesized_by="ai",
    )
    audit.log(repo_path, "save_synthesis", domain=domain, themes=len(key_themes))
    _auto_sync_after_write(repo_path, f"synthesis({domain}): cache update")
    return json.dumps({"status": "cached", "domain": domain, "synthesis": saved}, indent=2, ensure_ascii=False)


@mcp.tool()
def assess_risk_in_context(request: str, repo_path: str = ".") -> str:
    """
    Return rule-based risk (AUTHORITATIVE) + historical context for YOUR judgment.

    YOU may UPGRADE the risk (proceed → warn → ask → reject) if the historical
    context shows past incidents related to the request. You may NOT downgrade.

    If you upgrade to "ask" or "reject", call request_approval() before coding.
    """
    from precept.reasoning.impact_analyzer import ImpactAnalyzer
    from precept.reasoning.intent_analyzer import IntentAnalyzer
    from precept.reasoning.risk_scorer import RiskScorer

    _, scan, graph, store = _get_engine(repo_path)
    intent = IntentAnalyzer(scan).analyze(request)
    impact = ImpactAnalyzer(scan, graph).analyze(intent)
    risk = RiskScorer(scan).score(intent, impact)

    # gather historical context: memory entries that mention risk_pattern in same domain
    related = []
    for m in store.all():
        if not m.approved:
            continue
        if m.domain != intent.detected_domain and m.kind.value != "risk_pattern":
            continue
        text = (m.title + " " + m.body).lower()
        if any(kw in text for kw in (intent.detected_action, *intent.affected_areas)):
            related.append({
                "kind": m.kind.value,
                "title": m.title,
                "body": m.body[:200],
            })

    return json.dumps({
        "rule_based_decision": risk.decision.value,
        "rule_based_level": risk.level.value,
        "reasons": risk.reasons,
        "warnings": risk.warnings,
        "domain": intent.detected_domain,
        "historical_context": related,
        "rule": "AI may UPGRADE decision (proceed→warn→ask→reject) based on context. Never downgrade.",
        "instruction": (
            "Review historical_context. If past incidents touch this code path or domain, "
            "upgrade the decision and call request_approval() before coding."
        ),
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def get_module_context(module_path: str, repo_path: str = ".") -> str:
    """
    Return all known signals about a module so YOU can judge how risky it is to change.

    Signals (deterministic):
    - imported_by_count: how many files import this module
    - domains: which business domains this module belongs to
    - mentioned_in_memory: memory entries that reference this path
    - declared_critical: marked critical in workspace/link config
    - is_reusable_asset: appears in the reusable asset registry

    YOU should weigh these signals to decide if a change here needs extra scrutiny.
    """
    from precept.link.resolver import resolve_workspace

    _, scan, graph, store = _get_engine(repo_path)
    target = module_path.replace("\\", "/").lower()

    # find as reusable asset
    asset_match = None
    for a in scan.reusable_assets:
        if target in a.path.lower() or target == a.name.lower():
            asset_match = {"name": a.name, "type": a.asset_type, "path": a.path, "tags": a.tags}
            break

    # memory mentions
    memory_mentions = []
    for m in store.all():
        if not m.approved:
            continue
        if target in (m.body + m.title).lower():
            memory_mentions.append({"id": m.id, "title": m.title, "kind": m.kind.value})

    # workspace criticality
    res = resolve_workspace(repo_path)
    declared_critical = bool(res and res.link.critical)
    declared_domains = list(res.link.domains) if res else []

    # domain inference
    inferred_domains = [d for d in scan.domains if d in target]

    return json.dumps({
        "module_path": module_path,
        "is_reusable_asset": asset_match,
        "mentioned_in_memory": memory_mentions,
        "declared_critical": declared_critical,
        "declared_domains": declared_domains,
        "inferred_domains": inferred_domains,
        "instruction": (
            "Higher scrutiny if: declared_critical=true, OR mentioned in memory, OR "
            "spans multiple domains. Combine with assess_risk_in_context() if uncertain."
        ),
    }, indent=2, ensure_ascii=False)


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
    from precept.validation.code_validator import CodeValidator

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
    audit.log(repo_path, "validate_generated_code", language=language or scan.language, code_len=len(code), has_blockers=report.has_blockers)
    return json.dumps(out, indent=2, ensure_ascii=False)


@mcp.tool()
def list_approvals(status_filter: str = "pending", repo_path: str = ".") -> str:
    """
    List approval requests, filtered by status.
    status_filter: pending | approved | rejected | all
    """
    from precept.approval.queue import get_queue
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


# ==================================================================
# Skills — team-authored knowledge (markdown files in workspace/skills/)
# ==================================================================


@mcp.tool()
def list_skills(repo_path: str = ".") -> str:
    """
    List every team-authored skill (knowledge file) in the workspace.

    Skills are markdown files at <workspace>/skills/*.md with frontmatter
    (name + description). The descriptions tell you when each one applies —
    scan them and call read_skill(name) on any that sound relevant before
    writing code. Skills are how the team encodes conventions: UI style,
    money formatting, error handling patterns, deployment quirks, anything
    that an AI must know but isn't obvious from the code.
    """
    _auto_pull_workspace(repo_path)
    ws_name = _workspace_name_for(repo_path)
    if not ws_name:
        audit.log(repo_path, "list_skills", workspace=None, count=0)
        return json.dumps({
            "workspace": None,
            "skills": [],
            "note": "This repo is not linked to a workspace. Run `precept init` first.",
        }, indent=2, ensure_ascii=False)
    skills = load_workspace_skills(ws_name)
    audit.log(repo_path, "list_skills", workspace=ws_name, count=len(skills))
    return json.dumps({
        "workspace": ws_name,
        "count": len(skills),
        "skills": [
            {"name": s.name, "description": s.description, "tags": s.tags}
            for s in skills
        ],
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def read_skill(name: str, repo_path: str = ".") -> str:
    """
    Return the full body of a single team-authored skill by name.

    Call this after list_skills (or after seeing `available_skills` in
    analyze_intent) when a skill's description sounds relevant to the
    current task. The body is markdown — follow its guidance when writing
    code in the affected area.
    """
    ws_name = _workspace_name_for(repo_path)
    if not ws_name:
        audit.log(repo_path, "read_skill", name=name, found=False, reason="not_linked")
        return json.dumps({"error": "Repo not linked to a workspace."}, indent=2)
    skill = _read_skill(ws_name, name)
    if skill is None:
        audit.log(repo_path, "read_skill", name=name, found=False)
        return json.dumps({
            "error": f"Skill '{name}' not found",
            "hint": "Call list_skills to see what's available.",
        }, indent=2)
    audit.log(repo_path, "read_skill", name=name, found=True)
    return json.dumps({
        "name": skill.name,
        "description": skill.description,
        "tags": skill.tags,
        "body": skill.body,
        "source": skill.source_path,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def save_skill(
    name: str,
    description: str,
    body: str,
    tags: str = "",
    repo_path: str = ".",
) -> str:
    """
    Author or update a team skill (knowledge file). Writes
    `<workspace>/skills/<name>.md` with proper frontmatter, then auto-syncs
    to the team's git remote so everyone sees it immediately.

    Use this whenever the conversation surfaces a team rule, convention,
    style guide, or domain principle that future AI sessions should follow.
    Examples:
    - "All money is rendered as 'THB X,XXX.XX'" → save_skill('ui-money', '...', '...')
    - "Every POST mutation needs Idempotency-Key" → save_skill('billing', '...', '...')

    Args:
        name: kebab-case identifier — becomes `skills/<name>.md`. If it
              matches a built-in skill name (auth/payment/etc.), this entry
              overrides the built-in for the workspace.
        description: ONE short sentence describing when the skill applies.
              This is what future Claude sessions scan to decide whether to
              read the body — be specific and behavioral.
        body: full markdown content. Lists, code blocks, examples welcome.
        tags: comma-separated tags (optional)
        repo_path: defaults to cwd
    """

    ws_name = _workspace_name_for(repo_path)
    if not ws_name:
        return json.dumps({"error": "Repo not linked to a workspace. Run `precept init` first."}, indent=2)

    description = _sanitize_memory_text(description)
    body = _sanitize_memory_text(body)
    tags = _sanitize_memory_text(tags)

    from precept.paths import workspace_skills_dir
    skills_dir = workspace_skills_dir(ws_name)
    skills_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name).strip("-").lower()
    if not safe_name:
        return json.dumps({"error": "Invalid skill name."}, indent=2)
    target = skills_dir / f"{safe_name}.md"

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    fm_tags = "[" + ", ".join(f'"{t}"' for t in tag_list) + "]" if tag_list else "[]"

    content_lines = [
        "---",
        f"name: {safe_name}",
        f"description: {description.strip()}",
        f"tags: {fm_tags}",
        "---",
        "",
        body.strip(),
        "",
    ]
    target.write_text("\n".join(content_lines), encoding="utf-8")

    audit.log(repo_path, "save_skill", name=safe_name, len_body=len(body))
    _auto_sync_after_write(repo_path, f"skills: save {safe_name}")

    return json.dumps({
        "status": "saved",
        "name": safe_name,
        "path": str(target),
        "note": "Skill is now visible to every linked repo via list_skills + read_skill.",
    }, indent=2, ensure_ascii=False)
