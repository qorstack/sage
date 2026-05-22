"""
Approval queue — structured human-in-the-loop workflow.

AI submits an ApprovalRequest before proceeding on HIGH/CRITICAL risk actions.
Human reviews and calls approve() or reject().
AI polls or is notified of the outcome.

Stored in .knowlyx/approvals.json (same pattern as memory store).
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    id: str = ""
    title: str
    description: str
    risk_level: str
    domain: str
    repo_path: str = ""
    requested_action: str
    impact_summary: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewed_by: str = ""
    rejection_reason: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalQueue:
    def __init__(self, store_path: str | Path = ".knowlyx/approvals.json") -> None:
        self.path = Path(store_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def _flush(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")

    def _new_id(self) -> str:
        import hashlib, uuid
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        """Submit a new approval request. Returns the saved request with ID."""
        if not request.id:
            request.id = self._new_id()
        self._data[request.id] = request.model_dump(mode="json")
        self._flush()
        return request

    def approve(self, request_id: str, reviewed_by: str = "human") -> ApprovalRequest | None:
        raw = self._data.get(request_id)
        if not raw:
            return None
        req = ApprovalRequest(**raw)
        req.status = ApprovalStatus.APPROVED
        req.reviewed_by = reviewed_by
        req.reviewed_at = datetime.utcnow()
        self._data[request_id] = req.model_dump(mode="json")
        self._flush()
        return req

    def reject(self, request_id: str, reason: str = "", reviewed_by: str = "human") -> ApprovalRequest | None:
        raw = self._data.get(request_id)
        if not raw:
            return None
        req = ApprovalRequest(**raw)
        req.status = ApprovalStatus.REJECTED
        req.reviewed_by = reviewed_by
        req.rejection_reason = reason
        req.reviewed_at = datetime.utcnow()
        self._data[request_id] = req.model_dump(mode="json")
        self._flush()
        return req

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, request_id: str) -> ApprovalRequest | None:
        raw = self._data.get(request_id)
        return ApprovalRequest(**raw) if raw else None

    def pending(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._data.values() if r.get("status") == "pending"]

    def all(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._data.values()]

    def for_repo(self, repo_path: str) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._data.values() if r.get("repo_path") == repo_path]

    def status_of(self, request_id: str) -> ApprovalStatus | None:
        req = self.get(request_id)
        return req.status if req else None


def get_queue(repo_path: str = ".") -> ApprovalQueue:
    """
    Resolve approval queue path.

    If repo (or ancestor) has .knowlyx/config.toml, use the central
    workspace queue at ~/.knowlyx/workspaces/<name>/approvals.json
    — shared across all repos in the same workspace.
    Otherwise fall back to legacy per-repo .knowlyx/approvals.json.
    """
    from knowlyx.link.resolver import resolve_workspace_or_legacy

    _, approvals_path, _mode = resolve_workspace_or_legacy(repo_path)
    return ApprovalQueue(approvals_path)
