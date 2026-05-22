"""
Git-based sync for central workspace.

Wraps git commands so devs don't need to cd into ~/.knowlyx/workspaces/<name>/
every time. Also provides timestamp-based auto-merge for JSON conflicts
in memory.json / approvals.json — both files are flat dicts keyed by ID
so most "conflicts" are just additions from two devs.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from knowlyx.paths import workspace_dir


@dataclass
class SyncStatus:
    workspace: str
    path: Path
    has_remote: bool
    remote_url: str
    branch: str
    ahead: int
    behind: int
    dirty: bool
    unmerged: list[str]


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the completed process."""
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def auto_merge_json(path: Path) -> bool:
    """
    Resolve a git merge conflict in a JSON file that's a flat object
    keyed by stable ID (memory.json / approvals.json shape).

    Strategy: parse both sides of conflict markers, union by key.
    On key collision, prefer the entry with newer created_at / cached_at.

    Returns True if resolved cleanly, False if file has no conflict markers.
    """
    text = path.read_text(encoding="utf-8")
    if "<<<<<<<" not in text:
        return False

    ours: dict = {}
    theirs: dict = {}
    base_lines: list[str] = []
    state = "base"
    ours_chunk: list[str] = []
    theirs_chunk: list[str] = []

    for line in text.splitlines():
        if line.startswith("<<<<<<<"):
            state = "ours"
            continue
        if line.startswith("======="):
            state = "theirs"
            continue
        if line.startswith(">>>>>>>"):
            # try parsing each chunk as JSON fragment
            ours.update(_parse_partial_json(ours_chunk))
            theirs.update(_parse_partial_json(theirs_chunk))
            ours_chunk, theirs_chunk = [], []
            state = "base"
            continue
        if state == "ours":
            ours_chunk.append(line)
        elif state == "theirs":
            theirs_chunk.append(line)
        else:
            base_lines.append(line)

    # parse the non-conflict (base) parts as the bulk JSON
    base_text = "\n".join(base_lines)
    base: dict = {}
    try:
        # bracket the base to recover the dict (may be incomplete)
        base = _try_load_dict(base_text)
    except Exception:
        base = {}

    merged: dict = {}
    merged.update(base)
    for k, v in ours.items():
        merged[k] = _newer(merged.get(k), v)
    for k, v in theirs.items():
        merged[k] = _newer(merged.get(k), v)

    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return True


def _parse_partial_json(lines: list[str]) -> dict:
    """Lines may be entries like '"id": {...},' — wrap and parse."""
    raw = "\n".join(lines).strip().rstrip(",")
    if not raw:
        return {}
    try:
        return json.loads("{" + raw + "}")
    except json.JSONDecodeError:
        return {}


def _try_load_dict(text: str) -> dict:
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # may be missing the closing brace because of conflict cuts
        if text.endswith(","):
            text = text.rstrip(",")
        if not text.endswith("}"):
            text = text + "}"
        if not text.startswith("{"):
            text = "{" + text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}


def _newer(a: dict | None, b: dict) -> dict:
    if a is None:
        return b
    a_t = a.get("created_at") or a.get("cached_at") or ""
    b_t = b.get("created_at") or b.get("cached_at") or ""
    return b if b_t > a_t else a


class GitSync:
    """High-level wrapper for git ops on a central workspace folder."""

    MERGEABLE_FILES = ("memory.json", "approvals.json")

    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name
        self.path = workspace_dir(workspace_name)
        self.path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # State checks
    # ------------------------------------------------------------------

    def is_git_repo(self) -> bool:
        return (self.path / ".git").exists()

    def status(self) -> SyncStatus:
        if not self.is_git_repo():
            return SyncStatus(
                workspace=self.workspace_name,
                path=self.path,
                has_remote=False,
                remote_url="",
                branch="",
                ahead=0,
                behind=0,
                dirty=False,
                unmerged=[],
            )

        remote_url = ""
        try:
            r = _run(["remote", "get-url", "origin"], self.path, check=False)
            remote_url = r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            remote_url = ""

        branch = ""
        try:
            r = _run(["rev-parse", "--abbrev-ref", "HEAD"], self.path, check=False)
            branch = r.stdout.strip()
        except Exception:
            pass

        ahead = behind = 0
        try:
            r = _run(["rev-list", "--left-right", "--count", "@{u}...HEAD"], self.path, check=False)
            if r.returncode == 0:
                parts = r.stdout.split()
                behind, ahead = int(parts[0]), int(parts[1])
        except Exception:
            pass

        dirty = False
        unmerged: list[str] = []
        try:
            r = _run(["status", "--porcelain"], self.path, check=False)
            for line in r.stdout.splitlines():
                if not line.strip():
                    continue
                dirty = True
                code = line[:2]
                if "U" in code or code in ("AA", "DD"):
                    unmerged.append(line[3:].strip())
        except Exception:
            pass

        return SyncStatus(
            workspace=self.workspace_name,
            path=self.path,
            has_remote=bool(remote_url),
            remote_url=remote_url,
            branch=branch,
            ahead=ahead,
            behind=behind,
            dirty=dirty,
            unmerged=unmerged,
        )

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def init(self, remote_url: str = "", branch: str = "main") -> None:
        """git init + optional remote setup + .gitignore for scans/."""
        if not self.is_git_repo():
            _run(["init"], self.path)
            _run(["branch", "-M", branch], self.path, check=False)

        gitignore = self.path / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("scans/\n*.tmp\n.DS_Store\n", encoding="utf-8")

        if remote_url:
            r = _run(["remote"], self.path, check=False)
            if "origin" in (r.stdout or ""):
                _run(["remote", "set-url", "origin", remote_url], self.path)
            else:
                _run(["remote", "add", "origin", remote_url], self.path)

    # ------------------------------------------------------------------
    # Sync ops
    # ------------------------------------------------------------------

    def pull(self, auto_resolve: bool = True) -> tuple[bool, str]:
        """Pull. If conflicts in memory/approvals, auto-merge by timestamp."""
        if not self.is_git_repo():
            return False, "not a git repo — run `knowlyx sync init` first"

        r = _run(["pull", "--no-rebase"], self.path, check=False)
        if r.returncode == 0:
            return True, r.stdout.strip() or "Already up to date."

        # likely conflict — try to auto-resolve known files
        if not auto_resolve:
            return False, r.stdout + r.stderr

        resolved_any = False
        unresolvable: list[str] = []
        st = self.status()
        for rel in st.unmerged:
            full = self.path / rel
            if rel in self.MERGEABLE_FILES or full.name in self.MERGEABLE_FILES:
                if auto_merge_json(full):
                    _run(["add", rel], self.path, check=False)
                    resolved_any = True
                else:
                    unresolvable.append(rel)
            else:
                unresolvable.append(rel)

        if unresolvable:
            return False, (
                f"Auto-resolved JSON conflicts but these remain: {', '.join(unresolvable)}. "
                "Resolve manually, then run `git -C ... commit`."
            )

        if resolved_any:
            cm = _run(["commit", "--no-edit", "-m", "knowlyx: auto-merge memory/approvals"], self.path, check=False)
            if cm.returncode != 0:
                return False, cm.stdout + cm.stderr
            return True, "Conflicts auto-resolved (timestamp-merge)."

        return False, r.stdout + r.stderr

    def push(self, message: str = "knowlyx: update knowledge", auto_commit: bool = True) -> tuple[bool, str]:
        """Stage + commit dirty workspace, then push."""
        if not self.is_git_repo():
            return False, "not a git repo — run `knowlyx sync init` first"

        if auto_commit:
            st = self.status()
            if st.dirty:
                _run(["add", "-A"], self.path)
                cm = _run(["commit", "-m", message], self.path, check=False)
                # ok if nothing to commit
                if cm.returncode != 0 and "nothing to commit" not in (cm.stdout + cm.stderr):
                    return False, cm.stdout + cm.stderr

        r = _run(["push"], self.path, check=False)
        if r.returncode == 0:
            return True, r.stdout.strip() or "Pushed."
        return False, r.stdout + r.stderr
