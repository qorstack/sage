"""Tests for paths resolver — central knowledge store layout."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from knowlyx import paths


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """Point KNOWLYX_HOME at a temp dir so tests don't touch the real ~/.knowlyx."""
    monkeypatch.setenv("KNOWLYX_HOME", str(tmp_path / "knowlyx_home"))
    return tmp_path / "knowlyx_home"


def test_knowlyx_home_honors_env(isolated_home):
    assert paths.knowlyx_home() == isolated_home.resolve()


def test_knowlyx_home_default_is_user_home(monkeypatch):
    monkeypatch.delenv("KNOWLYX_HOME", raising=False)
    assert paths.knowlyx_home() == Path.home() / ".knowlyx"


def test_workspace_dir_path(isolated_home):
    assert paths.workspace_dir("foo") == isolated_home.resolve() / "workspaces" / "foo"


def test_ensure_workspace_dir_creates_structure(isolated_home):
    d = paths.ensure_workspace_dir("my-product")
    assert d.exists()
    assert (d / "scans").exists()
    assert (d / "packs").exists()


def test_workspace_paths_compose_correctly(isolated_home):
    paths.ensure_workspace_dir("alpha")
    assert paths.workspace_memory_path("alpha").name == "memory.json"
    assert paths.workspace_approvals_path("alpha").name == "approvals.json"
    assert paths.workspace_toml_path("alpha").name == "workspace.toml"
    assert paths.workspace_clones_path("alpha").name == "clones.json"


def test_list_workspaces_returns_existing(isolated_home):
    paths.ensure_workspace_dir("alpha")
    paths.ensure_workspace_dir("beta")
    names = paths.list_workspaces()
    assert names == ["alpha", "beta"]


def test_list_workspaces_empty_when_no_home(isolated_home):
    assert paths.list_workspaces() == []


def test_repo_link_config_path(tmp_path):
    assert paths.repo_link_config_path(tmp_path) == tmp_path / ".knowlyx" / "config.toml"
