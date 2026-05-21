"""Knowlyx REST API — same cognitive engine exposed over HTTP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from knowlyx.graph.cognitive_graph import CognitiveGraph
from knowlyx.reasoning.engine import ReasoningEngine
from knowlyx.scanner.repo_scanner import RepoScanner

app = FastAPI(
    title="Knowlyx API",
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
    return {"status": "ok", "service": "knowlyx"}


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
        from knowlyx.reasoning.impact_analyzer import ImpactAnalyzer
        from knowlyx.reasoning.intent_analyzer import IntentAnalyzer
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
