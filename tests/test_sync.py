"""Tests for git-sync JSON conflict merger.

We don't test actual git operations here (those need a real remote);
we focus on auto_merge_json which is the tricky part.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowai.sync.git_sync import auto_merge_json


def test_auto_merge_no_conflict_returns_false(tmp_path):
    f = tmp_path / "memory.json"
    f.write_text('{"a": {"title": "x"}}', encoding="utf-8")
    assert auto_merge_json(f) is False


def test_auto_merge_union_of_additions(tmp_path):
    """Both sides added different entries — union them."""
    f = tmp_path / "memory.json"
    f.write_text(
        '{\n'
        '  "common": {"title": "shared", "created_at": "2026-01-01"},\n'
        '<<<<<<< HEAD\n'
        '  "ours": {"title": "from us", "created_at": "2026-05-01"}\n'
        '=======\n'
        '  "theirs": {"title": "from them", "created_at": "2026-05-02"}\n'
        '>>>>>>> origin/main\n'
        '}\n',
        encoding="utf-8",
    )
    assert auto_merge_json(f) is True
    merged = json.loads(f.read_text(encoding="utf-8"))
    assert "ours" in merged
    assert "theirs" in merged


def test_auto_merge_picks_newer_on_collision(tmp_path):
    f = tmp_path / "memory.json"
    f.write_text(
        '{\n'
        '<<<<<<< HEAD\n'
        '  "same_id": {"title": "old", "created_at": "2026-01-01"}\n'
        '=======\n'
        '  "same_id": {"title": "newer", "created_at": "2026-05-01"}\n'
        '>>>>>>> origin/main\n'
        '}\n',
        encoding="utf-8",
    )
    auto_merge_json(f)
    merged = json.loads(f.read_text(encoding="utf-8"))
    assert merged["same_id"]["title"] == "newer"
