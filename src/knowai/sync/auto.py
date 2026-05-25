"""
Auto-sync helpers — keep the knowledge repo in sync with git without
asking the human to type `git pull` / `git push`.

Design goals:
- **Never lose data.** All writes happen locally first, then we attempt to
  push. If the network is down, the local change is still there.
- **Never block.** All git ops have short timeouts. Failures are logged and
  surfaced but never raise — auditing happens at the call site.
- **Opt-out friendly.** Set `KNOWLYX_AUTO_SYNC=0` to disable globally.
- **Silent on success.** Devs shouldn't see git noise when things work.

Public API:
    sync_enabled()         — is auto-sync turned on for this process?
    pull(workspace_dir)    — git pull --rebase --autostash, returns SyncResult
    push(workspace_dir,    — git add+commit+push, retries once on non-FF.
         files, message)
    full_sync(workspace_dir, message, files=...)
                           — pull → push. Used by `knowai sync`.

All helpers no-op (gracefully) when:
- the workspace folder isn't a git repo
- the repo has no `origin` remote
- KNOWLYX_AUTO_SYNC=0
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 15  # seconds — short enough to avoid hangs


@dataclass
class SyncResult:
    ok: bool
    action: str  # "pull" | "push" | "skip"
    detail: str = ""
    skipped_reason: str = ""


def sync_enabled() -> bool:
    """Honor KNOWLYX_AUTO_SYNC env var. Default: enabled."""
    val = os.environ.get("KNOWLYX_AUTO_SYNC", "1").strip().lower()
    return val not in ("0", "false", "no", "off")


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists() or _git(path, ["rev-parse", "--is-inside-work-tree"]).returncode == 0


def _has_remote(path: Path, remote: str = "origin") -> bool:
    r = _git(path, ["remote", "get-url", remote])
    return r.returncode == 0 and bool(r.stdout.strip())


def _git(cwd: Path, args: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        # Synthesize a failure result so callers don't need to handle exceptions.
        return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr=str(e))


def _skip(reason: str) -> SyncResult:
    return SyncResult(ok=True, action="skip", skipped_reason=reason)


def _preflight(workspace_dir: str | Path) -> tuple[Path, SyncResult | None]:
    """Common checks. Returns (path, skip_result) — if skip_result is not None, bail."""
    if not sync_enabled():
        return Path(workspace_dir), _skip("KNOWLYX_AUTO_SYNC=0")
    p = Path(workspace_dir).expanduser().resolve()
    if not p.exists():
        return p, _skip(f"path does not exist: {p}")
    if not _is_git_repo(p):
        return p, _skip("not a git repo")
    if not _has_remote(p):
        return p, _skip("no `origin` remote")
    return p, None


# ------------------------------------------------------------------
# Pull
# ------------------------------------------------------------------


def pull(workspace_dir: str | Path) -> SyncResult:
    """
    `git pull --rebase --autostash` — quietly bring local up to date with origin.

    Returns SyncResult.ok = False if rebase needs human intervention (conflict).
    The local working tree is left in the rebase-in-progress state so the user
    can resolve and continue.
    """
    p, skip = _preflight(workspace_dir)
    if skip is not None:
        return skip
    r = _git(p, ["pull", "--rebase", "--autostash", "origin"])
    if r.returncode == 0:
        return SyncResult(ok=True, action="pull", detail=(r.stdout or "").strip())
    # If rebase failed mid-way, abort it so the working tree is clean.
    in_rebase = (p / ".git" / "rebase-merge").exists() or (p / ".git" / "rebase-apply").exists()
    if in_rebase:
        _git(p, ["rebase", "--abort"], timeout=5)
    return SyncResult(
        ok=False,
        action="pull",
        detail=(r.stderr or r.stdout or "").strip(),
    )


# ------------------------------------------------------------------
# Push
# ------------------------------------------------------------------


def push(
    workspace_dir: str | Path,
    files: list[str] | None,
    message: str,
) -> SyncResult:
    """
    Stage `files` (or all changes if files is None), commit, and push to origin.

    Retries once with a pull-rebase + push on non-fast-forward rejection.
    Returns SyncResult.ok=True if push succeeded, .ok=False otherwise (local
    commit still exists; caller can surface "needs manual push").
    """
    p, skip = _preflight(workspace_dir)
    if skip is not None:
        return skip

    # Stage
    if files:
        add_args = ["add", "--", *files]
    else:
        add_args = ["add", "-A"]
    add = _git(p, add_args)
    if add.returncode != 0:
        return SyncResult(ok=False, action="push", detail=f"git add failed: {add.stderr.strip()}")

    # Anything to commit?
    status = _git(p, ["status", "--porcelain"])
    if not status.stdout.strip():
        # No changes — but check if there are unpushed commits we should push.
        unpushed = _git(p, ["log", "@{u}..HEAD", "--oneline"])
        if not unpushed.stdout.strip():
            return SyncResult(ok=True, action="push", detail="nothing to push")
    else:
        commit = _git(p, ["commit", "-m", message])
        if commit.returncode != 0:
            return SyncResult(ok=False, action="push", detail=f"git commit failed: {commit.stderr.strip()}")

    # Push, with one auto-retry on non-fast-forward.
    for attempt in range(2):
        pushed = _git(p, ["push", "origin", "HEAD"])
        if pushed.returncode == 0:
            return SyncResult(ok=True, action="push", detail="pushed")
        out = (pushed.stderr or "").lower()
        if attempt == 0 and ("non-fast-forward" in out or "rejected" in out or "fetch first" in out):
            # remote moved — rebase on top and try again
            rebase = pull(p)
            if not rebase.ok:
                return SyncResult(ok=False, action="push", detail=f"rebase failed during push retry: {rebase.detail}")
            continue
        return SyncResult(ok=False, action="push", detail=(pushed.stderr or pushed.stdout or "").strip())

    return SyncResult(ok=False, action="push", detail="push failed after retry")


# ------------------------------------------------------------------
# Composite
# ------------------------------------------------------------------


def full_sync(
    workspace_dir: str | Path,
    message: str = "",
    files: list[str] | None = None,
) -> tuple[SyncResult, SyncResult]:
    """
    Pull then push. Returns (pull_result, push_result).

    Used by both the `knowai sync` CLI command and the post-write hooks in
    `knowai memory decide`, `knowai approval ...`, and `knowai init`.
    """
    pr = pull(workspace_dir)
    if not pr.ok and pr.action != "skip":
        # If pull failed (conflict), don't try to push — surface the conflict.
        return pr, SyncResult(ok=False, action="push", detail="skipped: pull failed first")
    msg = message or "chore(knowai): auto-sync"
    push_result = push(workspace_dir, files, msg)
    _record_status(workspace_dir, pr, push_result)
    return pr, push_result


# ------------------------------------------------------------------
# Fire-and-forget background scheduling
# ------------------------------------------------------------------
#
# CLI commands and MCP tools call these instead of `full_sync` so they
# return to the user in milliseconds. The actual git work happens in a
# detached subprocess (CLI) or daemon thread (long-running MCP server).
# Result is written to `<workspace>/.knowai-sync-status.json` so
# `knowai doctor` can show what happened.


def schedule_full_sync(
    workspace_dir: str | Path,
    message: str = "",
    files: list[str] | None = None,
) -> None:
    """Schedule a pull+push in the background. Returns immediately."""
    if not sync_enabled():
        return
    p = Path(workspace_dir).expanduser().resolve()
    if not p.exists() or not _is_git_repo(p) or not _has_remote(p):
        return

    # Prefer detached subprocess so the sync survives even after the parent
    # CLI process exits. Daemon threads die when their parent does, which is
    # bad for short-lived CLI invocations.
    try:
        _spawn_detached_sync(p, message, files)
    except Exception:
        # As a last resort, fall back to a daemon thread (works for MCP).
        import threading
        threading.Thread(
            target=lambda: full_sync(p, message, files),
            daemon=True,
        ).start()


def _spawn_detached_sync(p: Path, message: str, files: list[str] | None) -> None:
    """Launch `python -m knowai.sync.auto _bg_sync <args>` detached."""
    import json as _json
    import sys
    payload = _json.dumps({"path": str(p), "message": message, "files": files or []})
    cmd = [sys.executable, "-m", "knowai.sync.auto", "_bg_sync", payload]
    kwargs: dict = dict(
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )
    if os.name == "nt":
        # Windows: fully detach from parent console.
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


def _record_status(
    workspace_dir: str | Path,
    pull_r: SyncResult,
    push_r: SyncResult,
) -> None:
    """Drop the result of a sync cycle so `knowai doctor` can read it."""
    import json as _json
    from datetime import datetime, timezone
    p = Path(workspace_dir) / ".knowai-sync-status.json"
    try:
        p.write_text(
            _json.dumps({
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "pull": {"ok": pull_r.ok, "action": pull_r.action, "detail": pull_r.detail},
                "push": {"ok": push_r.ok, "action": push_r.action, "detail": push_r.detail},
            }, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def last_sync_status(workspace_dir: str | Path) -> dict | None:
    import json as _json
    p = Path(workspace_dir) / ".knowai-sync-status.json"
    if not p.exists():
        return None
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError):
        return None


def _bg_main(argv: list[str]) -> int:
    """Entry point for `python -m knowai.sync.auto _bg_sync <json>`."""
    import json as _json
    if len(argv) < 2 or argv[0] != "_bg_sync":
        return 1
    try:
        payload = _json.loads(argv[1])
        full_sync(payload["path"], payload.get("message", ""), payload.get("files") or None)
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(_bg_main(sys.argv[1:]))
