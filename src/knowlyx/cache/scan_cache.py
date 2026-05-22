"""
Persistent scan cache for workspace repos.

Layout:
    ~/.knowlyx/workspaces/<workspace>/scans/<repo_name>.json

Purpose: dev clones only the repo they're working on. Knowlyx still
needs scan results for the other repos so AI can answer cross-repo
questions ("does the web repo have a useCheckout hook?").

Flow:
1. CI or tech lead runs `knowlyx workspace scan --persist` → writes
   all scans to central cache.
2. Other devs pull the workspace via git (or share otherwise).
3. WorkspaceScanner uses cached scan when a repo is not on local disk.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowlyx.models.schema import ScanResult
from knowlyx.paths import workspace_scans_dir


def _slug(repo_name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in repo_name)


class ScanCache:
    """Read/write cached scan results inside a central workspace."""

    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name
        self.dir = workspace_scans_dir(workspace_name)
        self.dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, repo_name: str) -> Path:
        return self.dir / f"{_slug(repo_name)}.json"

    def save(self, repo_name: str, scan: ScanResult) -> Path:
        path = self.path_for(repo_name)
        envelope = {
            "repo_name": repo_name,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "scan": json.loads(scan.model_dump_json()),
        }
        path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, repo_name: str) -> ScanResult | None:
        path = self.path_for(repo_name)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return ScanResult(**envelope["scan"])

    def metadata(self, repo_name: str) -> dict[str, Any] | None:
        path = self.path_for(repo_name)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return {
            "repo_name": envelope.get("repo_name", repo_name),
            "cached_at": envelope.get("cached_at"),
            "path": str(path),
        }

    def list_cached(self) -> list[str]:
        if not self.dir.exists():
            return []
        return sorted(p.stem for p in self.dir.glob("*.json"))

    def delete(self, repo_name: str) -> bool:
        path = self.path_for(repo_name)
        if path.exists():
            path.unlink()
            return True
        return False


def save_scan(workspace_name: str, repo_name: str, scan: ScanResult) -> Path:
    """Module-level helper — save a scan into the central cache."""
    return ScanCache(workspace_name).save(repo_name, scan)


def get_cached_scan(workspace_name: str, repo_name: str) -> ScanResult | None:
    """Module-level helper — fetch a cached scan if present."""
    return ScanCache(workspace_name).load(repo_name)
