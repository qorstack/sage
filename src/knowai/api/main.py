"""Knowai REST API — same cognitive engine exposed over HTTP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from knowai.graph.cognitive_graph import CognitiveGraph
from knowai.reasoning.engine import ReasoningEngine
from knowai.scanner.repo_scanner import RepoScanner

app = FastAPI(
    title="Knowai API",
    description="Cognitive enforcement layer for AI software development.",
    version="0.1.0",
)

_state: dict[str, Any] = {}


def _get_engine(repo_path: str):
    key = str(Path(repo_path).resolve())
    if key not in _state:
        scanner = RepoScanner(repo_path)
        scan = scanner.scan()
        graph = CognitiveGraph()
        graph.build(scan)
        engine = ReasoningEngine(scan, graph)
        _state[key] = (engine, scan, graph)
    return _state[key]


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    request: str
    repo_path: str = "."


class RepoRequest(BaseModel):
    repo_path: str = "."
    domain: str = ""


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok", "service": "knowai"}


@app.post("/analyze")
def analyze(body: AnalyzeRequest):
    """Full cognitive analysis for a user request."""
    try:
        engine, scan, _ = _get_engine(body.repo_path)
        report = engine.analyze(body.request)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan_repo(body: RepoRequest):
    """Scan a repository and return its cognitive profile."""
    try:
        scanner = RepoScanner(body.repo_path)
        result = scanner.scan()
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conventions")
def get_conventions(body: RepoRequest):
    """Return all detected conventions."""
    try:
        _, scan, _ = _get_engine(body.repo_path)
        return {
            "architecture": scan.architecture.value,
            "conventions": [c.model_dump() for c in scan.conventions],
            "forbidden_patterns": scan.forbidden_patterns,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets")
def get_assets(body: RepoRequest):
    """Return reusable assets, optionally filtered by domain."""
    try:
        _, scan, graph = _get_engine(body.repo_path)
        if body.domain:
            raw = graph.get_assets_for_domain(body.domain) + graph.find_reusable(body.domain)
            seen: set[str] = set()
            assets = []
            for r in raw:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    assets.append(r)
        else:
            assets = [a.model_dump() for a in scan.reusable_assets]
        return {"count": len(assets), "assets": assets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/impact")
def get_impact(body: AnalyzeRequest):
    """Return the blast radius of a change."""
    try:
        from knowai.reasoning.impact_analyzer import ImpactAnalyzer
        from knowai.reasoning.intent_analyzer import IntentAnalyzer
        _, scan, graph = _get_engine(body.repo_path)
        intent = IntentAnalyzer(scan).analyze(body.request)
        impact = ImpactAnalyzer(scan, graph).analyze(intent)
        return impact.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh")
def refresh(body: RepoRequest):
    """Force a fresh scan."""
    key = str(Path(body.repo_path).resolve())
    _state.pop(key, None)
    _, scan, graph = _get_engine(body.repo_path)
    return {"status": "refreshed", "domains": scan.domains, "graph": graph.summary()}


# ==================================================================
# Phase 2 — Memory + Packs
# ==================================================================


class MemorySaveRequest(BaseModel):
    domain: str
    title: str
    body: str
    kind: str = "business_context"  # business_context | team_decision | ...
    tags: list[str] = []
    repo_path: str = "."
    approved_by: str = ""


class MemoryApproveRequest(BaseModel):
    entry_id: str
    approved_by: str = "human"
    repo_path: str = "."


class MemorySearchRequest(BaseModel):
    query: str
    domain: str = ""
    repo_path: str = "."
    limit: int = 8


@app.post("/memory/save")
def memory_save(body: MemorySaveRequest):
    from knowai.memory.schema import MemoryEntry, MemoryKind
    from knowai.memory.store import create_store
    try:
        store = create_store(body.repo_path)
        try:
            kind = MemoryKind(body.kind)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown kind '{body.kind}'")
        entry = MemoryEntry(
            id="",
            kind=kind,
            domain=body.domain,
            title=body.title,
            body=body.body,
            tags=body.tags,
            approved=bool(body.approved_by) or kind == MemoryKind.TEAM_DECISION,
            approved_by=body.approved_by or ("team" if kind == MemoryKind.TEAM_DECISION else ""),
            repo_path=body.repo_path,
        )
        saved = store.save(entry)
        return {"id": saved.id, "approved": saved.approved}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/approve")
def memory_approve(body: MemoryApproveRequest):
    from knowai.memory.store import create_store
    try:
        store = create_store(body.repo_path)
        entry = store.get(body.entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="entry not found")
        entry.approved = True
        entry.approved_by = body.approved_by
        store.save(entry)
        return {"id": entry.id, "approved": True, "approved_by": entry.approved_by}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/recall")
def memory_recall(body: MemorySearchRequest):
    from knowai.memory.store import create_store
    try:
        store = create_store(body.repo_path)
        results = store.search(body.query, domain=body.domain, limit=body.limit)
        approved = [r for r in results if r.approved]
        return {"count": len(approved), "memories": [m.model_dump() for m in approved]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/list")
def memory_list(body: RepoRequest):
    from knowai.memory.store import create_store
    try:
        store = create_store(body.repo_path)
        entries = store.list_by_domain(body.domain) if body.domain else store.all()
        return {"count": len(entries), "entries": [e.model_dump() for e in entries]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{entry_id}")
def memory_forget(entry_id: str, repo_path: str = "."):
    from knowai.memory.store import create_store
    store = create_store(repo_path)
    return {"deleted": store.delete(entry_id), "id": entry_id}


@app.get("/packs/{domain}")
def get_pack(domain: str):
    from knowai.packs.builtin import get_pack as _get_pack
    pack = _get_pack(domain)
    if not pack:
        raise HTTPException(status_code=404, detail=f"no built-in pack for '{domain}'")
    return pack.model_dump()


# ==================================================================
# Phase 3 — Workspace + Approval
# ==================================================================


class WorkspaceRequest(BaseModel):
    workspace_path: str = "."


class CrossRepoImpactRequest(BaseModel):
    changed_repo: str
    change_description: str
    workspace_path: str = "."


class ApprovalRequestPayload(BaseModel):
    title: str
    description: str
    risk_level: str
    domain: str
    requested_action: str
    impact_summary: list[str] = []
    warnings: list[str] = []
    repo_path: str = "."


class ApprovalActionRequest(BaseModel):
    request_id: str
    reviewed_by: str = "human"
    reason: str = ""
    repo_path: str = "."


@app.post("/workspace/scan")
def workspace_scan(body: WorkspaceRequest):
    from knowai.workspace.config_loader import load
    from knowai.workspace.multi_scanner import WorkspaceScanner
    try:
        config = load(body.workspace_path)
        ws = WorkspaceScanner(config).scan()
        return ws.summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/impact")
def workspace_impact(body: CrossRepoImpactRequest):
    from knowai.workspace.config_loader import load
    from knowai.workspace.multi_scanner import CrossRepoImpactAnalyzer, WorkspaceScanner
    try:
        config = load(body.workspace_path)
        ws = WorkspaceScanner(config).scan()
        analyzer = CrossRepoImpactAnalyzer(ws, config)
        return analyzer.analyze(body.changed_repo, body.change_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approval/request")
def approval_request(body: ApprovalRequestPayload):
    from knowai.approval.queue import ApprovalRequest, get_queue
    queue = get_queue(body.repo_path)
    req = queue.submit(ApprovalRequest(
        title=body.title,
        description=body.description,
        risk_level=body.risk_level,
        domain=body.domain,
        repo_path=body.repo_path,
        requested_action=body.requested_action,
        impact_summary=body.impact_summary,
        warnings=body.warnings,
    ))
    return {"id": req.id, "status": req.status.value}


@app.get("/approval/{request_id}")
def approval_get(request_id: str, repo_path: str = "."):
    from knowai.approval.queue import get_queue
    queue = get_queue(repo_path)
    req = queue.get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="not found")
    return req.model_dump()


@app.post("/approval/approve")
def approval_approve(body: ApprovalActionRequest):
    from knowai.approval.queue import get_queue
    req = get_queue(body.repo_path).approve(body.request_id, body.reviewed_by)
    if not req:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": req.id, "status": req.status.value}


@app.post("/approval/reject")
def approval_reject(body: ApprovalActionRequest):
    from knowai.approval.queue import get_queue
    req = get_queue(body.repo_path).reject(body.request_id, body.reason, body.reviewed_by)
    if not req:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": req.id, "status": req.status.value, "reason": req.rejection_reason}


@app.get("/approval/list")
def approval_list(status_filter: str = "pending", repo_path: str = "."):
    from knowai.approval.queue import get_queue
    queue = get_queue(repo_path)
    entries = queue.pending() if status_filter == "pending" else (
        queue.all() if status_filter == "all" else
        [r for r in queue.all() if r.status.value == status_filter]
    )
    return {"count": len(entries), "requests": [r.model_dump() for r in entries]}


# ==================================================================
# Phase 4 — Validation
# ==================================================================


class ValidationRequest(BaseModel):
    code: str
    repo_path: str = "."
    language: str = ""


@app.post("/validate")
def validate(body: ValidationRequest):
    from knowai.validation.code_validator import CodeValidator
    try:
        _, scan, _ = _get_engine(body.repo_path)
        report = CodeValidator(scan).validate(body.code, language=body.language)
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
