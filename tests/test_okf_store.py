"""Tests for the OKF (Markdown) memory store."""

from __future__ import annotations

from precept.memory.okf_store import OkfMemoryStore, migrate_to_okf
from precept.memory.schema import MemoryEntry, MemoryKind, MemoryScope, MemorySource
from precept.memory.store import FileMemoryStore


def _entry(title="Use idempotency keys", domain="payment", **kw):
    base = dict(
        id="",
        kind=MemoryKind.TEAM_DECISION,
        domain=domain,
        title=title,
        body="All payment calls require an idempotency key.",
        tags=["payment", "safety"],
        scope=MemoryScope.WORKSPACE,
        workspace="acme",
        repo_name="api",
        source=MemorySource.AI,
        approved=True,
        approved_by="team",
        enforcement="block",
        applies_to=["payment", "payments/**"],
        related=["abc123"],
    )
    base.update(kw)
    return MemoryEntry(**base)


def test_roundtrip_preserves_all_fields(tmp_path):
    s = OkfMemoryStore(tmp_path / "agents" / "preceptai")
    saved = s.save(_entry())
    got = s.get(saved.id)
    assert got is not None
    assert got.title == "Use idempotency keys"
    assert got.body.startswith("All payment calls")
    assert got.tags == ["payment", "safety"]
    assert got.scope == MemoryScope.WORKSPACE
    assert got.workspace == "acme"
    assert got.repo_name == "api"
    assert got.source == MemorySource.AI
    assert got.approved is True
    assert got.approved_by == "team"
    assert got.enforcement == "block"
    assert got.applies_to == ["payment", "payments/**"]
    assert got.related == ["abc123"]


def test_layout_by_domain(tmp_path):
    root = tmp_path / "agents" / "preceptai"
    s = OkfMemoryStore(root)
    s.save(_entry())
    assert (root / "index.md").exists()
    assert (root / "payment" / "index.md").exists()
    assert list((root / "payment" / "decisions").glob("*.md"))


def test_list_search_delete(tmp_path):
    s = OkfMemoryStore(tmp_path / "okf")
    s.save(_entry(title="Use idempotency keys"))
    s.save(_entry(title="Refund window is 30 days", domain="payment"))
    assert len(s.list_by_domain("payment")) == 2
    hits = s.search("idempotent payment")
    assert hits and hits[0].title == "Use idempotency keys"
    target = s.search("refund window")[0]
    assert s.delete(target.id) is True
    assert s.get(target.id) is None


def test_mark_superseded_hides_from_all_but_get(tmp_path):
    s = OkfMemoryStore(tmp_path / "okf")
    old = s.save(_entry(title="Old rule"))
    new = s.save(_entry(title="New rule"))
    assert s.mark_superseded(old.id, new.id) is True
    titles = [e.title for e in s.all()]
    assert "Old rule" not in titles and "New rule" in titles
    assert s.get(old.id) is not None  # still retrievable directly


def test_synthesis(tmp_path):
    s = OkfMemoryStore(tmp_path / "okf")
    s.save(_entry())
    syn = s.save_synthesis("payment", "Payments need idempotency", ["idempotency"], ["which gateway?"])
    assert syn["summary"] == "Payments need idempotency"
    assert s.get_synthesis("payment")["key_themes"] == ["idempotency"]
    assert s.synthesis_stale("payment") is False
    s.save(_entry(title="Another"))  # new evidence -> stale
    assert s.synthesis_stale("payment") is True


def test_migrate_from_legacy_json(tmp_path):
    repo = tmp_path
    legacy = FileMemoryStore(repo / ".precept" / "memory")
    legacy.save(_entry(title="Legacy decision"))
    root = repo / "agents" / "preceptai"
    n = migrate_to_okf(repo, root)
    assert n == 1
    okf = OkfMemoryStore(root)
    assert "Legacy decision" in [e.title for e in okf.all()]
    # idempotent: re-running migrates nothing
    assert migrate_to_okf(repo, root) == 0
