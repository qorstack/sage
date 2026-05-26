"""Filesystem walking that prunes ignored dirs before descent and survives
vanished files (e.g. Next.js dev mode deletes transient rimraf shards
mid-scan, which crashes Path.rglob on Windows)."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Iterator

_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
    "build", ".next", ".nuxt", "coverage", ".pytest_cache", ".ruff_cache",
}


def safe_rglob(root: Path, pattern: str = "*") -> Iterator[Path]:
    """Yield Path objects under `root` matching `pattern`, pruning ignored dirs."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _e: None):
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
        base = Path(dirpath)
        # match dirs (so callers can find e.g. "generated" folders)
        for d in dirnames:
            if fnmatch.fnmatch(d, pattern):
                yield base / d
        for name in filenames:
            if fnmatch.fnmatch(name, pattern):
                yield base / name
