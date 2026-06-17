"""Memory entry types stored across sessions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryKind(str, Enum):
    BUSINESS_CONTEXT = "business_context"
    APPROVED_CONVENTION = "approved_convention"
    TEAM_DECISION = "team_decision"
    REUSABLE_ASSET = "reusable_asset"
    RISK_PATTERN = "risk_pattern"
    WORKFLOW = "workflow"


class MemoryScope(str, Enum):
    GLOBAL = "global"        # applies to every workspace
    WORKSPACE = "workspace"  # scoped to one workspace (must set `workspace`)


class MemorySource(str, Enum):
    HUMAN = "human"  # added by a person via dashboard / CLI
    AI = "ai"        # written by Claude (or other AI) through MCP


class MemoryEntry(BaseModel):
    id: str
    kind: MemoryKind
    domain: str
    title: str
    body: str
    tags: list[str] = Field(default_factory=list)
    approved_by: str = ""
    approved: bool = False
    repo_path: str = ""
    scope: MemoryScope = MemoryScope.GLOBAL
    source: MemorySource = MemorySource.HUMAN
    workspace: str = ""   # required when scope == WORKSPACE
    repo_name: str = ""   # set by AI auto-tagging from precept.config
    # Enforcement-aware fields — what makes a rule actionable, not just a doc.
    enforcement: str = "advise"          # advise | warn | block — how strictly the agent must apply it
    applies_to: list[str] = Field(default_factory=list)  # domains / file globs this entry governs
    supersedes: str = ""                 # id of an entry this one replaces
    related: list[str] = Field(default_factory=list)     # related entry ids (cognitive-graph edges)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
