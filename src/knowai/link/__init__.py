"""
Knowai Link layer — connects a project repo to a central workspace.

Each project repo gets `.knowai/config.toml` that points to a workspace
stored under `~/.knowai/workspaces/<name>/`. This lets devs clone one
repo at a time and still get shared memory, decisions, and cross-repo
topology.
"""

from knowai.link.config import LinkConfig, load_link, save_link
from knowai.link.resolver import (
    WorkspaceResolution,
    resolve_workspace,
    resolve_workspace_or_legacy,
    workspace_setup_hint,
)

__all__ = [
    "LinkConfig",
    "load_link",
    "save_link",
    "WorkspaceResolution",
    "resolve_workspace",
    "resolve_workspace_or_legacy",
    "workspace_setup_hint",
]
