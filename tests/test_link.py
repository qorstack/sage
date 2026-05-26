"""Tests for link config + workspace resolver."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowai import paths
from knowai.link.config import LinkConfig, load_link, save_link
from knowai.link.resolver import resolve_workspace, resolve_workspace_or_legacy


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLYX_HOME", str(tmp_path / "knowai_home"))
    # Force file-store path: tests in this module exercise the link/workspace
    # resolver, not Postgres. The repo's .env may leak POSTGRES_USER into the
    # shell, which would otherwise route create_store() to PostgresMemoryStore.
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    return tmp_path / "knowai_home"


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "api"
    r.mkdir()
    return r


def test_save_and_load_link(repo):
    cfg = LinkConfig(
        workspace="my-product",
        repo_name="api",
        role="backend",
        domains=["billing", "auth"],
        critical=True,
    )
    save_link(cfg, repo)

    loaded = load_link(repo)
    assert loaded is not None
    assert loaded.workspace == "my-product"
    assert loaded.repo_name == "api"
    assert loaded.role == "backend"
    assert loaded.domains == ["billing", "auth"]
    assert loaded.critical is True


def test_load_link_returns_none_when_missing(repo):
    assert load_link(repo) is None


def test_resolve_workspace_returns_none_for_unlinked_repo(repo, isolated_home):
    assert resolve_workspace(repo) is None


def test_resolve_workspace_finds_link_in_repo(repo, isolated_home):
    save_link(LinkConfig(workspace="alpha"), repo)
    res = resolve_workspace(repo)
    assert res is not None
    assert res.workspace_name == "alpha"
    assert res.workspace_dir == isolated_home.resolve() / "workspaces" / "alpha"
    # memory/approvals are per-entry directories now
    assert res.memory_path == res.workspace_dir / "memory"
    assert res.approvals_path == res.workspace_dir / "approvals"


def test_resolve_workspace_walks_up_to_ancestor(repo, isolated_home):
    save_link(LinkConfig(workspace="alpha"), repo)
    nested = repo / "src" / "deep" / "subdir"
    nested.mkdir(parents=True)
    res = resolve_workspace(nested)
    assert res is not None
    assert res.workspace_name == "alpha"
    assert res.repo_path == repo.resolve()


def test_resolve_workspace_or_legacy_central_mode(repo, isolated_home):
    save_link(LinkConfig(workspace="alpha"), repo)
    mem, app, mode = resolve_workspace_or_legacy(repo)
    assert mode == "central"
    assert mem == isolated_home.resolve() / "workspaces" / "alpha" / "memory"
    assert app == isolated_home.resolve() / "workspaces" / "alpha" / "approvals"


def test_resolve_workspace_or_legacy_legacy_mode(repo, isolated_home):
    mem, app, mode = resolve_workspace_or_legacy(repo)
    assert mode == "legacy"
    assert mem == repo / ".knowai" / "memory"
    assert app == repo / ".knowai" / "approvals"


def test_memory_store_uses_central_when_linked(repo, isolated_home):
    """Integration: create_store should follow the link to central memory."""
    from knowai.memory.schema import MemoryEntry, MemoryKind
    from knowai.memory.store import create_store

    save_link(LinkConfig(workspace="alpha"), repo)
    paths.ensure_workspace_dir("alpha")

    store = create_store(str(repo))
    entry = MemoryEntry(
        id="",
        kind=MemoryKind.TEAM_DECISION,
        domain="billing",
        title="test",
        body="body",
        approved=True,
    )
    store.save(entry)

    central_entries = isolated_home.resolve() / "workspaces" / "alpha" / "memory" / "entries"
    assert central_entries.exists()
    titles = [json.loads(p.read_text(encoding="utf-8"))["title"] for p in central_entries.glob("*.json")]
    assert "test" in titles

    legacy_entries = repo / ".knowai" / "memory" / "entries"
    assert not legacy_entries.exists()


def test_memory_store_uses_legacy_when_not_linked(repo, isolated_home):
    """Without link, behavior must match pre-Phase4 layout."""
    from knowai.memory.schema import MemoryEntry, MemoryKind
    from knowai.memory.store import create_store

    store = create_store(str(repo))
    entry = MemoryEntry(
        id="",
        kind=MemoryKind.TEAM_DECISION,
        domain="billing",
        title="legacy",
        body="body",
        approved=True,
    )
    store.save(entry)

    legacy_entries = repo / ".knowai" / "memory" / "entries"
    assert legacy_entries.exists()
    assert any(legacy_entries.glob("*.json"))


def test_approval_queue_uses_central_when_linked(repo, isolated_home):
    from knowai.approval.queue import ApprovalRequest, get_queue

    save_link(LinkConfig(workspace="alpha"), repo)
    paths.ensure_workspace_dir("alpha")

    queue = get_queue(str(repo))
    queue.submit(ApprovalRequest(
        title="test",
        description="d",
        risk_level="high",
        domain="billing",
        requested_action="x",
    ))

    central = isolated_home.resolve() / "workspaces" / "alpha" / "approvals"
    assert central.exists()
    assert any(central.glob("*.json"))
