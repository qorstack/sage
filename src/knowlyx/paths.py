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
    """Path to ~/.knowlyx/workspaces/<name>/ (does not create)."""
    return workspaces_root() / name


def ensure_workspace_dir(name: str) -> Path:
    """Create and return ~/.knowlyx/workspaces/<name>/."""
    d = workspace_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    (d / "scans").mkdir(exist_ok=True)
    (d / "packs").mkdir(exist_ok=True)
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


def list_workspaces() -> list[str]:
    """All workspace names present in ~/.knowlyx/workspaces/."""
    root = workspaces_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def repo_link_config_path(repo_path: str | Path) -> Path:
    """Per-repo .knowlyx/config.toml path."""
    return Path(repo_path) / ".knowlyx" / "config.toml"
