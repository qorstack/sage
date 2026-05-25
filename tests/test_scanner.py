"""Tests for the scanner layer."""

from pathlib import Path

import pytest

from knowai.scanner.repo_scanner import RepoScanner


def test_scan_knowai_itself(tmp_path):
    """Scanning the Knowai repo itself should return a valid ScanResult."""
    root = Path(__file__).parent.parent
    scanner = RepoScanner(root)
    result = scanner.scan()

    assert result.language == "python"
    assert result.framework == "fastapi"
    assert result.repo_path == str(root)


def test_scan_empty_dir(tmp_path):
    scanner = RepoScanner(tmp_path)
    result = scanner.scan()
    assert result.language == "unknown"
    assert result.conventions == []
    assert result.reusable_assets == []


def test_scan_node_project(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"next": "14.0.0", "react": "18.0.0"}, "devDependencies": {}}'
    )
    (tmp_path / "tsconfig.json").write_text("{}")
    scanner = RepoScanner(tmp_path)
    result = scanner.scan()
    assert result.language == "typescript"
    assert result.framework == "nextjs"
