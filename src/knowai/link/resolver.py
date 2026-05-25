"""
Resolve a repo_path to its central workspace (if any).

Resolution strategy:
1. Look for knowai.config in repo_path (or any parent up to FS root).
2. If found, return the workspace name + central paths.
3. If not found, return None — caller can fall back to legacy
   per-repo `<repo>/.knowai/memory.json` behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowai.link.config import LinkConfig, load_global_link, load_link
from knowai.paths import (
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
    """Walk up from `start` looking for knowai.config with `workspace` set."""
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

    Auto-creates the workspace directory if missing. CLI commands should
    call `workspace_setup_hint(repo_path)` separately to surface a clone
    instruction when a knowledge_remote is declared but the folder is empty.
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


def workspace_setup_hint(repo_path: str | Path = ".") -> str | None:
    """
    Return a one-line setup hint when the link declares a knowledge_remote
    but the local workspace folder is missing/empty — meaning the dev hasn't
    cloned the shared knowledge yet.

    Returns None when there's no hint to give (no link, no remote, or the
    workspace is already populated).
    """
    found = _find_link_upwards(Path(repo_path))
    if found is None:
        return None
    _, cfg = found
    if not cfg.knowledge_remote:
        return None
    ws_path = workspace_dir(cfg.workspace)
    if not ws_path.exists():
        target = str(ws_path)
        return (
            f"Shared knowledge for workspace '{cfg.workspace}' is not on this machine.\n"
            f"  Run:  git clone {cfg.knowledge_remote} {target}\n"
            "  (Then memory + approvals + decisions will be available to AI.)"
        )
    # exists but empty — likely the auto-created empty dir
    has_memory = (ws_path / "memory.json").exists()
    has_workspace_toml = (ws_path / "workspace.toml").exists()
    if not has_memory and not has_workspace_toml:
        target = str(ws_path)
        return (
            f"Workspace folder '{cfg.workspace}' exists but is empty (no memory.json).\n"
            f"  If this is a fresh setup, expected. Otherwise the team-shared knowledge\n"
            f"  hasn't been pulled. Replace the empty folder with a clone:\n"
            f"  rm -rf {target}\n"
            f"  git clone {cfg.knowledge_remote} {target}"
        )
    return None


def resolve_workspace_or_legacy(repo_path: str | Path = ".") -> tuple[Path, Path, str]:
    """
    Convenience: return (memory_path, approvals_path, mode).

    Resolution order:
    1. If repo (or ancestor) has `knowai.config` → "central" — use the
       linked workspace's shared store.
    2. If repo (or ancestor) has `workspace.toml` → "home" — we ARE the
       workspace home, store at workspace root.
    3. Otherwise "legacy" — per-repo `.knowai/memory/`.
    """
    res = resolve_workspace(repo_path)
    if res:
        return res.memory_path, res.approvals_path, "central"

    # Walk up looking for workspace.toml (knowledge-home mode)
    p = Path(repo_path).resolve()
    while True:
        if (p / "workspace.toml").exists():
            # paths.workspace_*_path now returns the dir, but we want this
            # specific knowledge-home folder, not the registry-resolved one.
            return p / "memory", p / "approvals", "home"
        if p.parent == p:
            break
        p = p.parent

    legacy_dir = Path(repo_path) / ".knowai"
    return legacy_dir / "memory", legacy_dir / "approvals", "legacy"


def _read_workspace_name(workspace_toml_dir: Path) -> str | None:
    """Best-effort read of the `name` field from `<dir>/workspace.toml`."""
    p = workspace_toml_dir / "workspace.toml"
    if not p.exists():
        return None
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("name") and "=" in line:
                _, _, v = line.partition("=")
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return None
