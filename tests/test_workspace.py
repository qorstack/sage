"""Tests for workspace and cross-repo analysis."""

from pathlib import Path

import pytest

from knowai.workspace.schema import RepoDependency, RepoConfig, RepoRole, WorkspaceConfig
from knowai.workspace.config_loader import save, load, init


def _make_repo(tmp_path: Path, name: str, package_json: dict | None = None) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    if package_json:
        import json
        (repo / "package.json").write_text(json.dumps(package_json))
    else:
        (repo / "pyproject.toml").write_text('[project]\nname = "x"\n[tool.fastapi]\n')
    return repo


def test_config_save_load(tmp_path):
    config = WorkspaceConfig(
        name="my-workspace",
        repos=[
            RepoConfig(name="api", path=str(tmp_path / "api"), role=RepoRole.BACKEND, domains=["payment", "auth"], critical=True),
            RepoConfig(name="web", path=str(tmp_path / "web"), role=RepoRole.FRONTEND),
        ],
        dependencies=[
            RepoDependency(from_repo="web", to_repo="api", dependency_type="api"),
        ],
    )
    saved_path = save(config, tmp_path)
    assert saved_path.exists()

    loaded = load(tmp_path)
    assert loaded.name == "my-workspace"
    assert len(loaded.repos) == 2
    assert len(loaded.dependencies) == 1
    assert loaded.repos[0].critical is True


def test_workspace_init(tmp_path):
    config = init(tmp_path, name="test-ws")
    assert config.name == "test-ws"
    assert (tmp_path / "knowai.toml").exists()


def test_get_dependents(tmp_path):
    config = WorkspaceConfig(
        name="ws",
        repos=[
            RepoConfig(name="api", path=".", role=RepoRole.BACKEND),
            RepoConfig(name="web", path=".", role=RepoRole.FRONTEND),
            RepoConfig(name="worker", path=".", role=RepoRole.WORKER),
        ],
        dependencies=[
            RepoDependency(from_repo="web", to_repo="api", dependency_type="api"),
            RepoDependency(from_repo="worker", to_repo="api", dependency_type="event"),
        ],
    )
    dependents = config.get_dependents("api")
    assert "web" in dependents
    assert "worker" in dependents


def test_workspace_scan(tmp_path):
    from knowai.workspace.multi_scanner import WorkspaceScanner

    api_dir = _make_repo(tmp_path, "api")
    web_dir = _make_repo(tmp_path, "web", {"dependencies": {"next": "14"}, "devDependencies": {}})

    config = WorkspaceConfig(
        name="test-ws",
        repos=[
            RepoConfig(name="api", path=str(api_dir), role=RepoRole.BACKEND),
            RepoConfig(name="web", path=str(web_dir), role=RepoRole.FRONTEND),
        ],
        dependencies=[RepoDependency(from_repo="web", to_repo="api", dependency_type="api")],
    )
    scanner = WorkspaceScanner(config)
    ws = scanner.scan()

    assert len(ws.repos) == 2
    assert ws.cross_repo_graph.number_of_nodes() == 2
    assert ws.cross_repo_graph.has_edge("web", "api")


def test_cross_repo_impact(tmp_path):
    from knowai.workspace.multi_scanner import CrossRepoImpactAnalyzer, WorkspaceScanner

    api_dir = _make_repo(tmp_path, "api")
    web_dir = _make_repo(tmp_path, "web", {"dependencies": {"next": "14"}, "devDependencies": {}})

    config = WorkspaceConfig(
        name="test-ws",
        repos=[
            RepoConfig(name="api", path=str(api_dir), role=RepoRole.BACKEND, critical=True),
            RepoConfig(name="web", path=str(web_dir), role=RepoRole.FRONTEND),
        ],
        dependencies=[RepoDependency(from_repo="web", to_repo="api")],
    )
    ws = WorkspaceScanner(config).scan()
    analyzer = CrossRepoImpactAnalyzer(ws, config)
    result = analyzer.analyze("api", "change payment DTO")

    assert result["changed_repo"] == "api"
    assert isinstance(result["all_affected_repos"], list)
