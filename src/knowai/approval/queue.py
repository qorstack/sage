"""
Approval queue — structured human-in-the-loop workflow.

Layout (conflict-free, file-per-request):

    <store_dir>/<id>.json

Two devs submitting approvals concurrently create different files → zero git
merge conflicts. Updating a request (approve/reject) touches only its own
file.

Legacy `approvals.json` (single file with `{id: req}` dict) is auto-migrated
on first init. The old file is renamed to `approvals.json.migrated`.

Fail-safe rule: once an approval is REJECTED, it stays REJECTED even if
someone later tries to approve it (security default).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from knowai.storage import atomic_write_text, file_lock


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


def _safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)


class ApprovalQueue:
    """Directory of per-request JSON files. Conflict-free across devs."""

    def __init__(self, store_dir: str | Path) -> None:
        p = Path(store_dir)
        if p.suffix == ".json":
            p = p.parent / p.stem  # approvals.json → approvals
        self.dir = p
        self.dir.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_json()

    # ------------------------------------------------------------------
    # Legacy migration
    # ------------------------------------------------------------------

    def _migrate_legacy_json(self) -> None:
        legacy = self.dir.parent / f"{self.dir.name}.json"
        if not legacy.exists():
            return
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(data, dict):
            for req_id, raw in data.items():
                if isinstance(raw, dict):
                    self._write_request(str(req_id), raw)
        try:
            legacy.rename(legacy.with_suffix(legacy.suffix + ".migrated"))
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Disk I/O
    # ------------------------------------------------------------------

    def _request_file(self, request_id: str) -> Path:
        return self.dir / f"{_safe_filename(request_id)}.json"

    def _write_request(self, request_id: str, payload: dict) -> None:
        path = self._request_file(request_id)
        with file_lock(path):
            atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def _read_request(self, request_id: str) -> dict | None:
        path = self._request_file(request_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def _load_all(self) -> list[dict]:
        if not self.dir.exists():
            return []
        out: list[dict] = []
        for p in self.dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    out.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return out

    @staticmethod
    def _new_id() -> str:
        import hashlib
        import uuid
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]

    # ------------------------------------------------------------------
    # Writes — each touches a single file under its own lock
    # ------------------------------------------------------------------

    def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        if not request.id:
            request.id = self._new_id()
        self._write_request(request.id, request.model_dump(mode="json"))
        return request

    def approve(self, request_id: str, reviewed_by: str = "human") -> ApprovalRequest | None:
        """Approve — but a previously REJECTED request stays rejected (fail-safe)."""
        path = self._request_file(request_id)
        with file_lock(path):
            raw = self._read_request(request_id)
            if not raw:
                return None
            existing = ApprovalRequest(**raw)
            if existing.status == ApprovalStatus.REJECTED:
                return existing  # fail-safe: do not flip
            existing.status = ApprovalStatus.APPROVED
            existing.reviewed_by = reviewed_by
            existing.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            atomic_write_text(path, json.dumps(existing.model_dump(mode="json"), indent=2, ensure_ascii=False, default=str))
            return existing

    def reject(self, request_id: str, reason: str = "", reviewed_by: str = "human") -> ApprovalRequest | None:
        """Reject — wins over a prior approve (security fail-safe)."""
        path = self._request_file(request_id)
        with file_lock(path):
            raw = self._read_request(request_id)
            if not raw:
                return None
            existing = ApprovalRequest(**raw)
            existing.status = ApprovalStatus.REJECTED
            existing.reviewed_by = reviewed_by
            existing.rejection_reason = reason or existing.rejection_reason
            existing.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            atomic_write_text(path, json.dumps(existing.model_dump(mode="json"), indent=2, ensure_ascii=False, default=str))
            return existing

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get(self, request_id: str) -> ApprovalRequest | None:
        raw = self._read_request(request_id)
        return ApprovalRequest(**raw) if raw else None

    def pending(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._load_all() if r.get("status") == "pending"]

    def all(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._load_all()]

    def for_repo(self, repo_path: str) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._load_all() if r.get("repo_path") == repo_path]

    def status_of(self, request_id: str) -> ApprovalStatus | None:
        req = self.get(request_id)
        return req.status if req else None


def get_queue(repo_path: str = ".") -> ApprovalQueue:
    """
    Resolve approval queue dir.

    If repo (or ancestor) has .knowai/config.toml, use the central
    workspace queue at <workspace>/approvals/ — shared across all repos.
    Otherwise fall back to legacy per-repo .knowai/approvals/.
    """
    from knowai.link.resolver import resolve_workspace_or_legacy

    _, approvals_path, _mode = resolve_workspace_or_legacy(repo_path)
    return ApprovalQueue(approvals_path)
