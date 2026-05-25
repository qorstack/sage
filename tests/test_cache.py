"""Tests for persistent scan cache."""

from __future__ import annotations

import pytest

from knowai.cache.scan_cache import ScanCache
from knowai.models.schema import ArchitecturePattern, ScanResult


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLYX_HOME", str(tmp_path / "knowai_home"))
    return tmp_path / "knowai_home"


def _make_scan(repo_path="/fake/repo", domains=None) -> ScanResult:
    return ScanResult(
        repo_path=repo_path,
        language="typescript",
        framework="nextjs",
        architecture=ArchitecturePattern.MODULAR_MONOLITH,
        domains=domains or ["billing"],
    )


def test_save_and_load_roundtrip(isolated_home):
    cache = ScanCache("alpha")
    cache.save("web", _make_scan(domains=["user", "checkout"]))

    loaded = cache.load("web")
    assert loaded is not None
    assert loaded.language == "typescript"
    assert loaded.framework == "nextjs"
    assert loaded.domains == ["user", "checkout"]


def test_load_missing_returns_none(isolated_home):
    assert ScanCache("alpha").load("nope") is None


def test_list_cached(isolated_home):
    cache = ScanCache("alpha")
    cache.save("api", _make_scan())
    cache.save("web", _make_scan())
    assert sorted(cache.list_cached()) == ["api", "web"]


def test_delete_removes_cache(isolated_home):
    cache = ScanCache("alpha")
    cache.save("api", _make_scan())
    assert cache.delete("api") is True
    assert cache.load("api") is None
    assert cache.delete("api") is False


def test_metadata_contains_timestamp(isolated_home):
    cache = ScanCache("alpha")
    cache.save("api", _make_scan())
    md = cache.metadata("api")
    assert md is not None
    assert "cached_at" in md
    assert md["repo_name"] == "api"


def test_slug_sanitizes_repo_names(isolated_home):
    cache = ScanCache("alpha")
    cache.save("my repo/with slashes", _make_scan())
    # should not throw, file lives under safe slug
    assert cache.load("my repo/with slashes") is not None
