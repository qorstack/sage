"""Tests for the memory layer."""

import pytest

from knowai.memory.schema import MemoryEntry, MemoryKind
from knowai.memory.store import FileMemoryStore


def test_save_and_retrieve(tmp_path):
    store = FileMemoryStore(tmp_path / "memory.json")
    entry = MemoryEntry(
        id="",
        kind=MemoryKind.BUSINESS_CONTEXT,
        domain="payment",
        title="Payment uses idempotency keys",
        body="Every payment creation must include an idempotency key to prevent duplicates.",
        approved=True,
        approved_by="human",
    )
    saved = store.save(entry)
    assert saved.id != ""
    retrieved = store.get(saved.id)
    assert retrieved is not None
    assert retrieved.title == entry.title


def test_search_by_keyword(tmp_path):
    store = FileMemoryStore(tmp_path / "memory.json")
    store.save(MemoryEntry(id="", kind=MemoryKind.TEAM_DECISION, domain="payment", title="Use idempotency", body="All payment calls need idempotency keys", approved=True, approved_by="team"))
    store.save(MemoryEntry(id="", kind=MemoryKind.BUSINESS_CONTEXT, domain="auth", title="OTP policy", body="OTP expires in 5 minutes", approved=True, approved_by="human"))

    results = store.search("payment idempotency")
    assert len(results) >= 1
    assert results[0].domain == "payment"


def test_unapproved_not_returned_after_filter(tmp_path):
    store = FileMemoryStore(tmp_path / "memory.json")
    store.save(MemoryEntry(id="", kind=MemoryKind.BUSINESS_CONTEXT, domain="auth", title="Draft rule", body="Not yet approved", approved=False))
    results = store.search("draft")
    approved = [r for r in results if r.approved]
    assert len(approved) == 0


def test_delete(tmp_path):
    store = FileMemoryStore(tmp_path / "memory.json")
    saved = store.save(MemoryEntry(id="", kind=MemoryKind.TEAM_DECISION, domain="order", title="Order state machine", body="...", approved=True, approved_by="team"))
    assert store.delete(saved.id)
    assert store.get(saved.id) is None


def test_list_by_domain(tmp_path):
    store = FileMemoryStore(tmp_path / "memory.json")
    store.save(MemoryEntry(id="", kind=MemoryKind.TEAM_DECISION, domain="payment", title="A", body="...", approved=True, approved_by="team"))
    store.save(MemoryEntry(id="", kind=MemoryKind.TEAM_DECISION, domain="auth", title="B", body="...", approved=True, approved_by="team"))
    results = store.list_by_domain("payment")
    assert len(results) == 1
    assert results[0].domain == "payment"


def test_persistence(tmp_path):
    path = tmp_path / "memory.json"
    store1 = FileMemoryStore(path)
    saved = store1.save(MemoryEntry(id="", kind=MemoryKind.TEAM_DECISION, domain="webhook", title="Use Redis queue", body="All webhooks go through BullMQ", approved=True, approved_by="team"))

    store2 = FileMemoryStore(path)
    retrieved = store2.get(saved.id)
    assert retrieved is not None
    assert retrieved.title == "Use Redis queue"
