"""Tests for the approve/reject fail-safe + concurrent safety."""

from __future__ import annotations

import threading

import pytest

from knowai.approval.queue import ApprovalQueue, ApprovalRequest, ApprovalStatus
from knowai.sync.git_sync import _newer


def _req(title="t") -> ApprovalRequest:
    return ApprovalRequest(
        title=title,
        description="d",
        risk_level="high",
        domain="billing",
        requested_action="x",
    )


def test_approve_then_reject_sticks_to_reject(tmp_path):
    q = ApprovalQueue(tmp_path / "approvals.json")
    req = q.submit(_req())
    q.approve(req.id, "alice")
    q.reject(req.id, reason="changed mind", reviewed_by="bob")

    final = q.get(req.id)
    assert final.status == ApprovalStatus.REJECTED
    assert final.rejection_reason == "changed mind"


def test_reject_then_approve_stays_rejected(tmp_path):
    """Fail-safe: once rejected, never auto-flipped to approved."""
    q = ApprovalQueue(tmp_path / "approvals.json")
    req = q.submit(_req())
    q.reject(req.id, reason="too risky", reviewed_by="bob")
    q.approve(req.id, "alice")  # should be a no-op for status

    final = q.get(req.id)
    assert final.status == ApprovalStatus.REJECTED
    assert final.rejection_reason == "too risky"


def test_concurrent_submits_no_lost(tmp_path):
    path = tmp_path / "approvals.json"

    def worker(prefix: str):
        q = ApprovalQueue(path)
        for i in range(20):
            q.submit(_req(title=f"{prefix}-{i}"))

    t1 = threading.Thread(target=worker, args=("A",))
    t2 = threading.Thread(target=worker, args=("B",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    final = ApprovalQueue(path)
    titles = {r.title for r in final.all()}
    assert len(titles) == 40


def test_sync_merge_prefers_rejected(tmp_path):
    """auto_merge_json — reject wins over approve regardless of timestamp."""
    older_reject = {"status": "rejected", "created_at": "2026-01-01"}
    newer_approve = {"status": "approved", "created_at": "2026-05-01"}
    assert _newer(older_reject, newer_approve) is older_reject

    # also true the other way around
    older_approve = {"status": "approved", "created_at": "2026-01-01"}
    newer_reject = {"status": "rejected", "created_at": "2026-05-01"}
    assert _newer(older_approve, newer_reject) is newer_reject


def test_sync_merge_normal_newer_wins(tmp_path):
    """Without rejection, normal newer-wins applies."""
    a = {"created_at": "2026-01-01"}
    b = {"created_at": "2026-05-01"}
    assert _newer(a, b) is b
