"""
Workspace registry — maps workspace name to its on-disk path.

Stored at ~/.knowlyx/registry.toml so the CLI can find a workspace by name
no matter where its files live (a cloned knowledge repo, a custom path, or
the default ~/.knowlyx/workspaces/<name>/).

Schema (TOML):
    [workspaces]
    tutorial = "C:/Me/PersonalCoding/tutorial-knowlyx/tutorial-knowlyx-knowledge"
    other    = "/home/me/.knowlyx/workspaces/other"

Resolution order in paths.workspace_dir(name):
    1. registry entry (if present and the path still exists)
    2. ~/.knowlyx/workspaces/<name>/  (default)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowlyx.paths import knowlyx_home


def _registry_path() -> Path:
    return knowlyx_home() / "registry.toml"


def _load_raw() -> dict[str, str]:
    p = _registry_path()
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    try:
        import tomllib  # py3.11+
        data: dict[str, Any] = tomllib.loads(text)
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
            data = tomllib.loads(p.read_bytes())
        except ImportError:
            data = _simple_parse(text)
    ws = data.get("workspaces", {})
    if not isinstance(ws, dict):
        return {}
    return {str(k): str(v) for k, v in ws.items()}


def _simple_parse(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"workspaces": {}}
    section: str | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            result.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if section:
            result[section][k] = v
        else:
            result[k] = v
    return result


def _save_raw(entries: dict[str, str]) -> Path:
    p = _registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Knowlyx workspace registry — maps workspace name to on-disk path.",
        "# Managed by `knowlyx init` and `knowlyx workspace register`.",
        "",
        "[workspaces]",
    ]
    for name, path in sorted(entries.items()):
        safe = path.replace("\\", "/")
        lines.append(f'{name} = "{safe}"')
    lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def get_path(name: str) -> Path | None:
    """Return the registered path for workspace `name`, if any."""
    entries = _load_raw()
    raw = entries.get(name)
    if not raw:
        return None
    return Path(raw).expanduser()


def register(name: str, path: str | Path) -> Path:
    """Add or update a workspace name → path mapping."""
    entries = _load_raw()
    entries[name] = str(Path(path).expanduser().resolve())
    return _save_raw(entries)


def unregister(name: str) -> bool:
    """Remove a workspace from the registry. Returns True if it existed."""
    entries = _load_raw()
    if name not in entries:
        return False
    del entries[name]
    _save_raw(entries)
    return True


def list_registered() -> dict[str, Path]:
    return {k: Path(v) for k, v in _load_raw().items()}
