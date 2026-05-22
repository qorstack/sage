"""
Resolve a repo_path to its central workspace (if any).

Resolution strategy:
1. Look for .knowlyx/config.toml in repo_path (or any parent up to FS root).
2. If found, return the workspace name + central paths.
3. If not found, return None — caller can fall back to legacy
   per-repo `<repo>/.knowlyx/memory.json` behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowlyx.link.config import LinkConfig, load_link
from knowlyx.paths import (
    ensure_workspace_dir,
    workspace_approvals_path,
    workspace_dir,
    workspace_memory_path,
)


@dataclass
class WorkspaceResolution:
    workspace_name: str
    workspace_dir: Path
    memory_path: Path
    approvals_path: Path
    link: LinkConfig
    repo_path: Path


def _find_link_upwards(start: Path) -> tuple[Path, LinkConfig] | None:
    """Walk up from `start` looking for .knowlyx/config.toml. Return (repo_root, config)."""
    p = start.resolve()
    while True:
        cfg = load_link(p)
        if cfg is not None:
            return p, cfg
        if p.parent == p:
            return None
        p = p.parent


def resolve_workspace(repo_path: str | Path = ".") -> WorkspaceResolution | None:
    """
    Return WorkspaceResolution if repo (or any ancestor) has a link config.
    Returns None if no link found — caller should fall back to legacy mode.
    """
    found = _find_link_upwards(Path(repo_path))
    if found is None:
        return None
    repo_root, cfg = found
    ws_dir = ensure_workspace_dir(cfg.workspace)
    return WorkspaceResolution(
        workspace_name=cfg.workspace,
        workspace_dir=ws_dir,
        memory_path=workspace_memory_path(cfg.workspace),
        approvals_path=workspace_approvals_path(cfg.workspace),
        link=cfg,
        repo_path=repo_root,
    )


def resolve_workspace_or_legacy(repo_path: str | Path = ".") -> tuple[Path, Path, str]:
    """
    Convenience: return (memory_path, approvals_path, mode) where
    mode is "central" if a workspace was resolved, else "legacy".

    Legacy paths preserve original per-repo behavior:
        <repo_path>/.knowlyx/memory.json
        <repo_path>/.knowlyx/approvals.json
    """
    res = resolve_workspace(repo_path)
    if res:
        return res.memory_path, res.approvals_path, "central"
    legacy_dir = Path(repo_path) / ".knowlyx"
    return legacy_dir / "memory.json", legacy_dir / "approvals.json", "legacy"
