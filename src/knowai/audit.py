"""
Lightweight audit trail for MCP tool calls.

Goal: let users verify, after the fact, that the AI actually called Knowai
tools — and which ones. Each tool call appends one JSON line to:

    <repo>/.knowai/audit.log

To keep the file bounded, we cap at KNOWLYX_AUDIT_MAX lines (default 500) —
oldest lines are dropped when we exceed the cap. No external rotation tools
needed, no per-day files, no growing disk usage.

Log format (one JSON object per line):

    {"ts":"2026-05-22T10:31:04Z","tool":"analyze_intent","args":{"request":"add /orders","decision":"warn"}}

Each entry is small (~200 bytes), so 500 lines ≈ 100 KB.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MAX_LINES = 500


def _audit_path(repo_path: str | Path) -> Path:
    return Path(repo_path) / ".knowai" / "audit.log"


def _max_lines() -> int:
    raw = os.environ.get("KNOWLYX_AUDIT_MAX", "")
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return _DEFAULT_MAX_LINES


def log(repo_path: str | Path, tool: str, **args: Any) -> None:
    """
    Append one event to the audit log. Failures are silent — auditing
    must NEVER break a tool call.
    """
    try:
        path = _audit_path(repo_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool": tool,
            "args": {k: _truncate(v) for k, v in args.items() if v is not None and v != ""},
        }
        line = json.dumps(entry, ensure_ascii=False)
        # Append, then cap by line count.
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        _maybe_truncate(path)
    except Exception:
        pass


def _truncate(value: Any, max_chars: int = 200) -> Any:
    """Trim long strings so the log stays compact."""
    if isinstance(value, str) and len(value) > max_chars:
        return value[:max_chars] + "…"
    return value


def _maybe_truncate(path: Path) -> None:
    """If line count exceeds the cap, keep only the last N lines."""
    cap = _max_lines()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= cap:
            return
        kept = lines[-cap:]
        path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    except Exception:
        pass


def read(repo_path: str | Path, limit: int = 50) -> list[dict[str, Any]]:
    """Return the last `limit` events (most recent first). Empty list if no log."""
    path = _audit_path(repo_path)
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for raw in reversed(lines):
        if len(out) >= limit:
            break
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out


def clear(repo_path: str | Path) -> bool:
    """Delete the audit log. Returns True if a file existed."""
    path = _audit_path(repo_path)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except Exception:
        return False
