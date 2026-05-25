"""Tests for memory schema v2 — entries + syntheses + stale tracking + migration."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from knowai.memory.schema import MemoryEntry, MemoryKind
from knowai.memory.store import FileMemoryStore


def _entry(domain="billing", title="t", body="b", approved=True) -> MemoryEntry:
    return MemoryEntry(
        id="",
        kind=MemoryKind.TEAM_DECISION,
        domain=domain,
        title=title,
        body=body,
        approved=approved,
    )


def test_v2_schema_on_first_save(tmp_path):
    """First save creates a per-entry file in <store>/entries/."""
    store = FileMemoryStore(tmp_path / "mem")
    store.save(_entry(title="first"))

    entries_dir = tmp_path / "mem" / "entries"
    assert entries_dir.exists()
    files = list(entries_dir.glob("*.json"))
    assert len(files) == 1
    raw = json.loads(files[0].read_text(encoding="utf-8"))
    assert raw["title"] == "first"


def test_migrates_v1_to_v2_on_load(tmp_path):
    """Legacy single-file v1 memory.json is split into per-entry files on load."""
    legacy_path = tmp_path / "mem.json"
    legacy = {
        "abc123": {
            "id": "abc123",
            "kind": "team_decision",
            "domain": "billing",
            "title": "old",
            "body": "old body",
            "approved": True,
            "tags": [],
            "approved_by": "",
            "repo_path": "",
            "created_at": "2026-01-01T00:00:00",
            "metadata": {},
        }
    }
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")

    # passing the legacy .json path is accepted: store uses parent/stem dir
    store = FileMemoryStore(legacy_path)
    entries = store.all()
    assert len(entries) == 1
    assert entries[0].title == "old"

    # legacy file renamed, per-entry file exists
    assert (tmp_path / "mem.json.migrated").exists()
    assert (tmp_path / "mem" / "entries" / "abc123.json").exists()


def test_save_marks_existing_synthesis_stale(tmp_path):
    store = FileMemoryStore(tmp_path / "mem.json")
    store.save(_entry(title="first"))

    # cache a synthesis
    store.save_synthesis(
        domain="billing",
        summary="all about billing",
        key_themes=["stripe"],
        open_questions=[],
    )
    assert store.synthesis_stale("billing") is False

    # new entry arrives — synthesis should become stale
    store.save(_entry(title="second"))
    assert store.synthesis_stale("billing") is True


def test_save_synthesis_caches_then_recall(tmp_path):
    store = FileMemoryStore(tmp_path / "mem.json")
    store.save(_entry(title="e1"))
    saved = store.save_synthesis(
        domain="billing",
        summary="summary text",
        key_themes=["a", "b"],
        open_questions=["q?"],
    )
    assert saved["stale"] is False
    assert saved["entry_count_at_synthesis"] == 1

    fetched = store.get_synthesis("billing")
    assert fetched["summary"] == "summary text"
    assert fetched["key_themes"] == ["a", "b"]


def test_synthesis_stale_when_no_synthesis(tmp_path):
    store = FileMemoryStore(tmp_path / "mem.json")
    store.save(_entry())
    assert store.synthesis_stale("billing") is True


def test_concurrent_saves_no_lost_updates(tmp_path):
    """Two threads each save 30 entries with different IDs — all must persist."""
    store_path = tmp_path / "mem.json"

    def worker(prefix: str):
        # each thread re-instantiates store (simulates separate processes)
        s = FileMemoryStore(store_path)
        for i in range(30):
            s.save(_entry(domain="billing", title=f"{prefix}-{i}", body=str(i)))

    t1 = threading.Thread(target=worker, args=("A",))
    t2 = threading.Thread(target=worker, args=("B",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    final = FileMemoryStore(store_path)
    all_entries = final.all()
    titles = {e.title for e in all_entries}
    # 30 from A + 30 from B = 60 unique titles (different IDs)
    assert len(titles) == 60


def test_delete_removes_entry(tmp_path):
    store = FileMemoryStore(tmp_path / "mem.json")
    saved = store.save(_entry(title="to-delete"))
    assert store.delete(saved.id) is True
    assert store.get(saved.id) is None
    assert store.delete(saved.id) is False
