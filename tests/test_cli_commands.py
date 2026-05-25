"""Smoke tests for new CLI commands via Typer's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from knowai.cli.main import app


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLYX_HOME", str(tmp_path / "knowai_home"))
    return tmp_path / "knowai_home"


runner = CliRunner()


def test_workspace_create_then_list(isolated_home):
    r = runner.invoke(app, ["workspace", "create", "my-product"])
    assert r.exit_code == 0
    assert "my-product" in r.output

    r2 = runner.invoke(app, ["workspace", "list"])
    assert r2.exit_code == 0
    assert "my-product" in r2.output


def test_link_then_unlink(isolated_home, tmp_path):
    runner.invoke(app, ["workspace", "create", "alpha"])

    repo = tmp_path / "api"
    repo.mkdir()

    r = runner.invoke(app, ["link", "alpha", "--repo", str(repo), "--role", "backend"])
    assert r.exit_code == 0
    assert (repo / ".knowai" / "config.toml").exists()

    r2 = runner.invoke(app, ["unlink", "--repo", str(repo)])
    assert r2.exit_code == 0
    assert not (repo / ".knowai" / "config.toml").exists()


def test_link_fails_when_workspace_missing(isolated_home, tmp_path):
    repo = tmp_path / "api"
    repo.mkdir()
    r = runner.invoke(app, ["link", "does-not-exist", "--repo", str(repo)])
    assert r.exit_code != 0


def test_commit_check_no_stamp_warns(isolated_home, tmp_path):
    repo = tmp_path / "api"
    repo.mkdir()
    r = runner.invoke(app, ["commit-check", "--repo", str(repo)])
    assert r.exit_code == 0  # non-strict
    assert "No cognition stamp" in r.output


def test_commit_check_strict_fails_without_stamp(isolated_home, tmp_path):
    repo = tmp_path / "api"
    repo.mkdir()
    r = runner.invoke(app, ["commit-check", "--repo", str(repo), "--strict"])
    assert r.exit_code == 1


def test_commit_check_proceeds_on_approved_stamp(isolated_home, tmp_path):
    from datetime import datetime, timezone
    repo = tmp_path / "api"
    (repo / ".knowai").mkdir(parents=True)
    (repo / ".knowai" / "last_cognition.json").write_text(json.dumps({
        "request": "test",
        "decision": "proceed",
        "risk_level": "low",
        "domain": "billing",
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }), encoding="utf-8")

    r = runner.invoke(app, ["commit-check", "--repo", str(repo), "--strict"])
    assert r.exit_code == 0
    assert "OK" in r.output


def test_commit_check_blocks_on_reject(isolated_home, tmp_path):
    from datetime import datetime, timezone
    repo = tmp_path / "api"
    (repo / ".knowai").mkdir(parents=True)
    (repo / ".knowai" / "last_cognition.json").write_text(json.dumps({
        "request": "drop table users",
        "decision": "reject",
        "risk_level": "critical",
        "domain": "billing",
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }), encoding="utf-8")

    r = runner.invoke(app, ["commit-check", "--repo", str(repo)])
    assert r.exit_code == 1
    assert "REJECTED" in r.output


def test_sync_status_for_uninitialized_workspace(isolated_home):
    runner.invoke(app, ["workspace", "create", "alpha"])
    r = runner.invoke(app, ["sync", "status", "--workspace", "alpha"])
    assert r.exit_code == 0
    assert "not git-initialized" in r.output


def test_init_without_link_prints_suggestions(isolated_home, tmp_path):
    repo = tmp_path / "api"
    repo.mkdir()
    (repo / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    r = runner.invoke(app, ["init", "--repo", str(repo)])
    assert r.exit_code == 0
    # init now suggests either --knowledge (be the workspace) or --link (join one)
    assert "--knowledge" in r.output
    assert "--link" in r.output
