"""
Central path resolver for Knowlyx user-level storage.

Layout:
    ~/.knowlyx/
      workspaces/
        <workspace_name>/
          workspace.toml      - topology (which repos exist + dependencies)
          memory.json         - shared decisions across all repos
          approvals.json      - shared approval queue
          packs/              - team-custom cognition packs (optional)
          scans/              - per-repo scan cache (Phase 4.B)
          clones.json         - registry: repo_name -> local clone path

Per-project:
    <project-repo>/
      .knowlyx/
        config.toml           - pointer to central workspace
        cache/                - per-repo local cache (optional)

Environment override: KNOWLYX_HOME can override ~/.knowlyx
"""

from __future__ import annotations

import os
from pathlib import Path


def knowlyx_home() -> Path:
    """User-level Knowlyx home. Honors KNOWLYX_HOME env var."""
    env = os.environ.get("KNOWLYX_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".knowlyx"


def workspaces_root() -> Path:
    return knowlyx_home() / "workspaces"


def workspace_dir(name: str) -> Path:
    """
    Path to the workspace folder for `name`.

    Resolution: checks the registry (~/.knowlyx/registry.toml) first — if
    the workspace is registered at a custom path (e.g. inside a cloned
    knowledge repo) AND that path still exists, return it. Otherwise fall
    back to the default ~/.knowlyx/workspaces/<name>/.

    Does NOT create the directory.
    """
    # Local import to avoid circular dependency: registry.py imports knowlyx_home.
    try:
        from knowlyx.registry import get_path
        registered = get_path(name)
        if registered is not None and registered.exists():
            return registered
    except Exception:
        pass
    return workspaces_root() / name


def ensure_workspace_dir(name: str, at: str | Path | None = None) -> Path:
    """
    Create and return the workspace folder for `name`.

    If `at` is given, create the workspace there and register it. Otherwise
    follow the same resolution as workspace_dir() (registry → default).
    """
    if at is not None:
        d = Path(at).expanduser().resolve()
        d.mkdir(parents=True, exist_ok=True)
        try:
            from knowlyx.registry import register
            register(name, d)
        except Exception:
            pass
    else:
        d = workspace_dir(name)
        d.mkdir(parents=True, exist_ok=True)
    (d / "scans").mkdir(exist_ok=True)
    (d / "skills").mkdir(exist_ok=True)
    return d


def workspace_memory_path(name: str) -> Path:
    return workspace_dir(name) / "memory.json"


def workspace_approvals_path(name: str) -> Path:
    return workspace_dir(name) / "approvals.json"


def workspace_toml_path(name: str) -> Path:
    return workspace_dir(name) / "workspace.toml"


def workspace_clones_path(name: str) -> Path:
    return workspace_dir(name) / "clones.json"


def workspace_scans_dir(name: str) -> Path:
    return workspace_dir(name) / "scans"


def workspace_skills_dir(name: str) -> Path:
    """User-authored knowledge skills (markdown + frontmatter)."""
    return workspace_dir(name) / "skills"


def list_workspaces() -> list[str]:
    """All workspace names present in ~/.knowlyx/workspaces/."""
    root = workspaces_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def repo_link_config_path(repo_path: str | Path) -> Path:
    """Per-repo .knowlyx/config.toml path."""
    return Path(repo_path) / ".knowlyx" / "config.toml"
