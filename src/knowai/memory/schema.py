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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
