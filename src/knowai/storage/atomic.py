"""
Cross-platform file locking + atomic writes.

Guarantees:
- `file_lock(path)` — exclusive lock, works on Windows (msvcrt) and POSIX (fcntl)
- `atomic_write_text(path, text)` — write-temp-then-rename (atomic on same filesystem)
- `read_modify_write(path, mutator)` — lock + read + mutate + atomic write
  Solves the lost-update problem when two processes save the same JSON file.

No external deps — uses stdlib only.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

# ------------------------------------------------------------------
# Lock implementation
# ------------------------------------------------------------------

if sys.platform == "win32":
    import msvcrt

    def _lock_fd(fd: int) -> None:
        # blocking lock on first byte
        while True:
            try:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
                return
            except OSError:
                time.sleep(0.05)

    def _unlock_fd(fd: int) -> None:
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _lock_fd(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_EX)

    def _unlock_fd(fd: int) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


@contextmanager
def file_lock(path: str | Path, timeout: float = 30.0) -> Iterator[None]:
    """
    Acquire an exclusive lock on a sidecar file `<path>.lock`.

    Two processes calling file_lock(same_path) will serialize.
    The sidecar approach lets the actual data file be replaced atomically
    (via rename) without breaking the lock.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lock_path = p.with_suffix(p.suffix + ".lock")
    # touch
    lock_path.touch(exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR)
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                _lock_fd(fd)
                break
            except (BlockingIOError, OSError):
                if time.monotonic() > deadline:
                    raise TimeoutError(f"could not acquire lock on {lock_path} within {timeout}s")
                time.sleep(0.05)
        yield
    finally:
        try:
            _unlock_fd(fd)
        finally:
            os.close(fd)


# ------------------------------------------------------------------
# Atomic write
# ------------------------------------------------------------------


def atomic_write_text(path: str | Path, text: str, encoding: str = "utf-8") -> None:
    """
    Write text atomically: write to temp in same dir, then os.replace.
    os.replace is atomic on POSIX and Windows (same volume) — readers
    see either the old or new content, never a half-written file.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # mkstemp in same dir guarantees same filesystem
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{p.name}.",
        suffix=".tmp",
        dir=str(p.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as f:
            f.write(text)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        os.replace(tmp_name, str(p))
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ------------------------------------------------------------------
# Composite: lock + read + mutate + atomic write
# ------------------------------------------------------------------


def read_modify_write(
    path: str | Path,
    mutator: Callable[[dict], dict],
    *,
    default: dict | None = None,
    timeout: float = 30.0,
) -> dict:
    """
    Atomically read JSON from `path`, pass to mutator, write result back.
    Returns the final dict.

    Safe under concurrent processes — the lock prevents lost updates.
    """
    p = Path(path)
    with file_lock(p, timeout=timeout):
        current: dict
        if p.exists():
            try:
                current = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(current, dict):
                    current = default if default is not None else {}
            except (json.JSONDecodeError, OSError):
                current = default if default is not None else {}
        else:
            current = default if default is not None else {}

        updated = mutator(current)
        if not isinstance(updated, dict):
            raise TypeError("mutator must return a dict")

        atomic_write_text(p, json.dumps(updated, indent=2, ensure_ascii=False, default=str))
        return updated
