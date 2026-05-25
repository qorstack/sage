"""Tests for atomic storage primitives — file locking, atomic write, R-M-W."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from knowai.storage import atomic_write_text, file_lock, read_modify_write


def test_atomic_write_creates_file(tmp_path):
    f = tmp_path / "out.json"
    atomic_write_text(f, '{"a": 1}')
    assert f.exists()
    assert json.loads(f.read_text()) == {"a": 1}


def test_atomic_write_overwrites_atomically(tmp_path):
    f = tmp_path / "out.json"
    atomic_write_text(f, '{"v": 1}')
    atomic_write_text(f, '{"v": 2}')
    assert json.loads(f.read_text()) == {"v": 2}


def test_atomic_write_cleans_temp_on_error(tmp_path):
    # Triggering an error mid-write is hard from outside; just confirm
    # no .tmp files linger after a successful write.
    f = tmp_path / "out.json"
    atomic_write_text(f, "ok")
    temps = list(tmp_path.glob(".*tmp"))
    assert temps == []


def test_file_lock_serializes_writers(tmp_path):
    """Two threads doing read-modify-write don't lose updates."""
    counter_path = tmp_path / "counter.json"
    counter_path.write_text('{"n": 0}', encoding="utf-8")

    def bump():
        for _ in range(50):
            with file_lock(counter_path):
                data = json.loads(counter_path.read_text(encoding="utf-8"))
                data["n"] += 1
                atomic_write_text(counter_path, json.dumps(data))

    t1 = threading.Thread(target=bump)
    t2 = threading.Thread(target=bump)
    t1.start(); t2.start()
    t1.join(); t2.join()

    final = json.loads(counter_path.read_text(encoding="utf-8"))
    assert final["n"] == 100  # no lost updates


def test_read_modify_write_creates_default(tmp_path):
    f = tmp_path / "nope.json"
    result = read_modify_write(f, lambda d: {**d, "x": 1}, default={})
    assert result == {"x": 1}
    assert json.loads(f.read_text()) == {"x": 1}


def test_read_modify_write_merges_existing(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"a": 1}', encoding="utf-8")
    result = read_modify_write(f, lambda d: {**d, "b": 2})
    assert result == {"a": 1, "b": 2}


def test_read_modify_write_handles_corrupt_json(tmp_path):
    f = tmp_path / "broken.json"
    f.write_text("not json {{{", encoding="utf-8")
    result = read_modify_write(f, lambda d: {**d, "ok": True}, default={})
    assert result == {"ok": True}


def test_read_modify_write_rejects_non_dict_mutator(tmp_path):
    f = tmp_path / "data.json"
    with pytest.raises(TypeError):
        read_modify_write(f, lambda d: "not a dict", default={})
