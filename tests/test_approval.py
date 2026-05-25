"""Tests for the approval queue."""

from knowai.approval.queue import ApprovalQueue, ApprovalRequest, ApprovalStatus


def _queue(tmp_path):
    return ApprovalQueue(tmp_path / "approvals.json")


def test_submit_and_get(tmp_path):
    queue = _queue(tmp_path)
    req = queue.submit(ApprovalRequest(
        title="Deploy payment fix",
        description="Fix for payment scan 501",
        risk_level="high",
        domain="payment",
        requested_action="modify payment handler",
    ))
    assert req.id
    assert req.status == ApprovalStatus.PENDING

    found = queue.get(req.id)
    assert found is not None
    assert found.title == "Deploy payment fix"


def test_approve(tmp_path):
    queue = _queue(tmp_path)
    req = queue.submit(ApprovalRequest(title="Test", description="", risk_level="medium", domain="auth", requested_action="add route"))
    approved = queue.approve(req.id, "alice")
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.reviewed_by == "alice"


def test_reject_with_reason(tmp_path):
    queue = _queue(tmp_path)
    req = queue.submit(ApprovalRequest(title="Risky", description="", risk_level="critical", domain="payment", requested_action="drop table"))
    rejected = queue.reject(req.id, reason="Too dangerous", reviewed_by="bob")
    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.rejection_reason == "Too dangerous"


def test_pending_filter(tmp_path):
    queue = _queue(tmp_path)
    r1 = queue.submit(ApprovalRequest(title="A", description="", risk_level="low", domain="user", requested_action="add field"))
    r2 = queue.submit(ApprovalRequest(title="B", description="", risk_level="high", domain="payment", requested_action="fix"))
    queue.approve(r2.id)

    pending = queue.pending()
    assert len(pending) == 1
    assert pending[0].id == r1.id


def test_persistence(tmp_path):
    path = tmp_path / "approvals.json"
    q1 = ApprovalQueue(path)
    req = q1.submit(ApprovalRequest(title="Persist", description="", risk_level="medium", domain="auth", requested_action="add route"))

    q2 = ApprovalQueue(path)
    found = q2.get(req.id)
    assert found is not None
    assert found.title == "Persist"
