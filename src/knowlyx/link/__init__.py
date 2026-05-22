"""
Knowlyx Link layer — connects a project repo to a central workspace.

Each project repo gets `.knowlyx/config.toml` that points to a workspace
stored under `~/.knowlyx/workspaces/<name>/`. This lets devs clone one
repo at a time and still get shared memory, decisions, and cross-repo
topology.
"""

from knowlyx.link.config import LinkConfig, load_link, save_link
from knowlyx.link.resolver import (
    WorkspaceResolution,
    resolve_workspace,
    resolve_workspace_or_legacy,
)

__all__ = [
    "LinkConfig",
    "load_link",
    "save_link",
    "WorkspaceResolution",
    "resolve_workspace",
    "resolve_workspace_or_legacy",
]
