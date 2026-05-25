"""Load and save knowai.toml workspace config."""

from __future__ import annotations

from pathlib import Path

from knowai.workspace.schema import RepoConfig, RepoDependency, RepoRole, WorkspaceConfig

_DEFAULT_FILENAME = "knowai.toml"


def load(workspace_path: str | Path = ".") -> WorkspaceConfig:
    """
    Load knowai.toml from workspace_path. Returns empty config if not found.

    Resolution order:
    1. If workspace_path/knowai.toml exists → load that (legacy/sibling layout)
    2. Else if workspace_path (or ancestor) is a linked repo → load central
       ~/.knowai/workspaces/<name>/workspace.toml
    3. Else return empty config named after the folder
    """
    root = Path(workspace_path).resolve()
    toml_file = root / _DEFAULT_FILENAME
    if toml_file.exists():
        return _read_toml(toml_file, root)

    # Try central lookup via link config
    from knowai.link.resolver import resolve_workspace
    res = resolve_workspace(workspace_path)
    if res is not None:
        central = res.workspace_dir / "workspace.toml"
        if central.exists():
            return _read_toml(central, res.workspace_dir)

    return WorkspaceConfig(name=root.name)


def load_central(workspace_name: str) -> WorkspaceConfig:
    """Load workspace.toml directly from ~/.knowai/workspaces/<name>/."""
    from knowai.paths import workspace_dir, workspace_toml_path
    toml_file = workspace_toml_path(workspace_name)
    if not toml_file.exists():
        return WorkspaceConfig(name=workspace_name)
    return _read_toml(toml_file, workspace_dir(workspace_name))


def _read_toml(toml_file: Path, root: Path) -> WorkspaceConfig:
    try:
        import tomllib  # Python 3.11+
        data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
    except ImportError:
        try:
            import tomli as tomllib
            data = tomllib.loads(toml_file.read_bytes())
        except ImportError:
            data = _simple_toml_parse(toml_file.read_text(encoding="utf-8"))
    return _parse(data, root)


def save(config: WorkspaceConfig, workspace_path: str | Path = ".") -> Path:
    """Serialize config to knowai.toml + write any embedded repos as per-file
    entries under <workspace>/repos/. This keeps the round-trip stable:
    `load(save(cfg)).repos == cfg.repos`."""
    root = Path(workspace_path).resolve()
    toml_file = root / _DEFAULT_FILENAME
    toml_file.write_text(_serialize(config), encoding="utf-8")
    if config.repos:
        repos_dir = root / "repos"
        repos_dir.mkdir(parents=True, exist_ok=True)
        for repo in config.repos:
            (repos_dir / f"{_safe_repo_filename(repo.name)}.toml").write_text(
                _serialize_repo(repo), encoding="utf-8"
            )
    return toml_file


def init(workspace_path: str | Path = ".", name: str = "") -> WorkspaceConfig:
    """Create a minimal knowai.toml in workspace_path."""
    root = Path(workspace_path).resolve()
    config = WorkspaceConfig(name=name or root.name)
    save(config, root)
    return config


def register_repo_in_workspace(
    workspace_name: str,
    repo: RepoConfig,
) -> tuple[bool, Path | None]:
    """
    Auto-add or update a repo entry as `<workspace>/repos/<repo_name>.toml`.

    One file per repo so two devs linking concurrently never collide on the
    same line of `workspace.toml`. Returns (changed, written_path).
    `written_path` is None if the workspace folder doesn't exist locally
    (caller should print the clone hint).
    """
    from knowai.paths import workspace_toml_path

    toml_path = workspace_toml_path(workspace_name)
    if not toml_path.exists():
        return False, None

    ws_dir = toml_path.parent
    repos_dir = ws_dir / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)
    repo_file = repos_dir / f"{_safe_repo_filename(repo.name)}.toml"

    # Merge with existing per-repo entry if any.
    existing = _read_repo_file(repo_file) if repo_file.exists() else None
    if existing is not None:
        merged = RepoConfig(
            name=repo.name,
            path=existing.path,
            git_url=repo.git_url or existing.git_url,
            role=repo.role if repo.role != RepoRole.UNKNOWN else existing.role,
            domains=list({*existing.domains, *repo.domains}),
            tags=list({*existing.tags, *repo.tags}),
            critical=repo.critical or existing.critical,
            description=repo.description or existing.description,
        )
        if merged == existing:
            return False, repo_file
        target = merged
    else:
        target = repo

    repo_file.write_text(_serialize_repo(target), encoding="utf-8")
    return True, repo_file


def _safe_repo_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def _serialize_repo(repo: RepoConfig) -> str:
    """Serialize a single repo as a flat TOML file (no `[[repos]]` header).
    Uses TOML literal strings (single-quoted) so Windows paths with backslashes
    don't get interpreted as escape sequences."""
    lines = [f"name = '{repo.name}'"]
    if repo.git_url:
        lines.append(f"git_url = '{repo.git_url}'")
    if repo.path:
        lines.append(f"path = '{repo.path}'")
    if repo.role != RepoRole.UNKNOWN:
        lines.append(f"role = '{repo.role.value}'")
    if repo.domains:
        lines.append("domains = [" + ", ".join(f"'{d}'" for d in repo.domains) + "]")
    if repo.tags:
        lines.append("tags = [" + ", ".join(f"'{t}'" for t in repo.tags) + "]")
    if repo.critical:
        lines.append("critical = true")
    if repo.description:
        lines.append(f"description = '{repo.description}'")
    lines.append("")
    return "\n".join(lines)


def _read_repo_file(path: Path) -> RepoConfig | None:
    try:
        try:
            import tomllib
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore
                data = tomllib.loads(path.read_bytes())
            except ImportError:
                # Crude fallback for flat TOML.
                data = {}
                for raw in path.read_text(encoding="utf-8").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip()
                    if v.startswith("[") and v.endswith("]"):
                        inner = v[1:-1]
                        data[k] = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
                    elif v in ("true", "false"):
                        data[k] = v == "true"
                    else:
                        data[k] = v.strip('"').strip("'")
    except OSError:
        return None
    if not data.get("name"):
        return None
    return RepoConfig(
        name=str(data["name"]),
        path=str(data.get("path", "")),
        git_url=str(data.get("git_url", "")),
        role=RepoRole(data.get("role", "unknown")) if data.get("role", "unknown") in [r.value for r in RepoRole] else RepoRole.UNKNOWN,
        domains=list(data.get("domains", []) or []),
        tags=list(data.get("tags", []) or []),
        critical=bool(data.get("critical", False)),
        description=str(data.get("description", "")),
    )


def _load_repos_from_dir(workspace_dir: Path) -> list[RepoConfig]:
    """Read every `<workspace>/repos/*.toml` as a RepoConfig."""
    repos_dir = workspace_dir / "repos"
    if not repos_dir.exists():
        return []
    out: list[RepoConfig] = []
    for p in sorted(repos_dir.glob("*.toml")):
        cfg = _read_repo_file(p)
        if cfg is not None:
            out.append(cfg)
    return out


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

def _parse(data: dict, root: Path) -> WorkspaceConfig:
    # Legacy [[repos]] blocks still inline in workspace.toml — we'll migrate
    # them to per-file storage below.
    inline_repos = [
        RepoConfig(
            name=r["name"],
            path=str(root / r["path"]) if r.get("path") else "",
            git_url=r.get("git_url", ""),
            role=RepoRole(r.get("role", "unknown")),
            domains=r.get("domains", []),
            tags=r.get("tags", []),
            critical=r.get("critical", False),
            description=r.get("description", ""),
        )
        for r in data.get("repos", [])
    ]

    # Authoritative source: per-file repos under <workspace>/repos/.
    per_file_repos = _load_repos_from_dir(root)
    per_file_names = {r.name for r in per_file_repos}

    # If workspace.toml still has inline [[repos]] (older workspaces), split
    # them into per-file storage. Per-file wins on name conflict.
    for r in inline_repos:
        if r.name in per_file_names:
            continue
        try:
            (root / "repos").mkdir(parents=True, exist_ok=True)
            (root / "repos" / f"{_safe_repo_filename(r.name)}.toml").write_text(
                _serialize_repo(r), encoding="utf-8"
            )
            per_file_repos.append(r)
        except OSError:
            # Read-only workspace? Keep using inline data this run.
            per_file_repos.append(r)

    repos = sorted(per_file_repos, key=lambda r: r.name)

    deps = [
        RepoDependency(
            from_repo=d["from"],
            to_repo=d["to"],
            dependency_type=d.get("type", "api"),
            description=d.get("description", ""),
        )
        for d in data.get("dependencies", [])
    ]
    return WorkspaceConfig(
        name=data.get("name", root.name),
        version=str(data.get("version", "1")),
        description=data.get("description", ""),
        repos=repos,
        dependencies=deps,
        global_conventions=data.get("global_conventions", []),
        metadata=data.get("metadata", {}),
    )


def _serialize(config: WorkspaceConfig) -> str:
    """
    Serialize the workspace header to `workspace.toml`. Per-repo entries live
    in `repos/<name>.toml` and are NOT written here — that's how concurrent
    `knowai init` calls from different devs avoid colliding on the same file.
    """
    lines = [
        f'name = "{config.name}"',
        f'version = "{config.version}"',
        f'description = "{config.description}"',
        "",
    ]
    if config.global_conventions:
        lines.append("global_conventions = [")
        for c in config.global_conventions:
            lines.append(f'  "{c}",')
        lines.append("]")
        lines.append("")
    for dep in config.dependencies:
        lines.append("[[dependencies]]")
        lines.append(f'from = "{dep.from_repo}"')
        lines.append(f'to = "{dep.to_repo}"')
        lines.append(f'type = "{dep.dependency_type}"')
        if dep.description:
            lines.append(f'description = "{dep.description}"')
        lines.append("")
    return "\n".join(lines)


def _simple_toml_parse(text: str) -> dict:
    """Minimal TOML parser fallback (handles only flat keys and [[array]])."""
    result: dict = {"repos": [], "dependencies": []}
    current_section: dict | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[["):
            key = line.strip("[]").strip()
            current_section = {}
            result.setdefault(key, []).append(current_section)
        elif line.startswith("["):
            current_section = None
        elif "=" in line:
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if current_section is not None:
                current_section[k] = v
            else:
                result[k] = v
    return result
