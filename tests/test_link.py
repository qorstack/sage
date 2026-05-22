"""Tests for link config + workspace resolver."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowlyx import paths
from knowlyx.link.config import LinkConfig, load_link, save_link
from knowlyx.link.resolver import resolve_workspace, resolve_workspace_or_legacy


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLYX_HOME", str(tmp_path / "knowlyx_home"))
    return tmp_path / "knowlyx_home"


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
    assert res.memory_path == res.workspace_dir / "memory.json"
    assert res.approvals_path == res.workspace_dir / "approvals.json"


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
    assert mem == isolated_home.resolve() / "workspaces" / "alpha" / "memory.json"
    assert app == isolated_home.resolve() / "workspaces" / "alpha" / "approvals.json"


def test_resolve_workspace_or_legacy_legacy_mode(repo, isolated_home):
    mem, app, mode = resolve_workspace_or_legacy(repo)
    assert mode == "legacy"
    assert mem == repo / ".knowlyx" / "memory.json"
    assert app == repo / ".knowlyx" / "approvals.json"


def test_memory_store_uses_central_when_linked(repo, isolated_home):
    """Integration: create_store should follow the link to central memory."""
    from knowlyx.memory.schema import MemoryEntry, MemoryKind
    from knowlyx.memory.store import create_store

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

    central_memory = isolated_home.resolve() / "workspaces" / "alpha" / "memory.json"
    assert central_memory.exists()
    data = json.loads(central_memory.read_text(encoding="utf-8"))
    assert any(v["title"] == "test" for v in data.values())

    legacy_memory = repo / ".knowlyx" / "memory.json"
    assert not legacy_memory.exists()


def test_memory_store_uses_legacy_when_not_linked(repo, isolated_home):
    """Without link, behavior must match pre-Phase4 layout."""
    from knowlyx.memory.schema import MemoryEntry, MemoryKind
    from knowlyx.memory.store import create_store

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

    legacy_memory = repo / ".knowlyx" / "memory.json"
    assert legacy_memory.exists()


def test_approval_queue_uses_central_when_linked(repo, isolated_home):
    from knowlyx.approval.queue import ApprovalRequest, get_queue

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

    central = isolated_home.resolve() / "workspaces" / "alpha" / "approvals.json"
    assert central.exists()
