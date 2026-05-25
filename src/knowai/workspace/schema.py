"""Workspace schema — defines a multi-repo project."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RepoRole(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    WORKER = "worker"
    GATEWAY = "gateway"
    SHARED = "shared"
    INFRA = "infra"
    UNKNOWN = "unknown"


class RepoDependency(BaseModel):
    """Declares that repo A depends on repo B (e.g. consumes its API)."""
    from_repo: str
    to_repo: str
    dependency_type: str = "api"  # api | event | shared_db | package
    description: str = ""


class RepoConfig(BaseModel):
    name: str
    path: str = ""
    """Local filesystem path (varies per dev — optional, can be overridden locally)."""
    git_url: str = ""
    """Canonical git remote URL — the portable cross-machine identifier."""
    role: RepoRole = RepoRole.UNKNOWN
    domains: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    critical: bool = False
    description: str = ""


class WorkspaceConfig(BaseModel):
    name: str
    version: str = "1"
    description: str = ""
    repos: list[RepoConfig] = Field(default_factory=list)
    dependencies: list[RepoDependency] = Field(default_factory=list)
    global_conventions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_repo(self, name: str) -> RepoConfig | None:
        return next((r for r in self.repos if r.name == name), None)

    def get_dependents(self, repo_name: str) -> list[str]:
        """Return repos that depend on the given repo."""
        return [d.from_repo for d in self.dependencies if d.to_repo == repo_name]

    def get_dependencies_of(self, repo_name: str) -> list[str]:
        """Return repos that the given repo depends on."""
        return [d.to_repo for d in self.dependencies if d.from_repo == repo_name]
