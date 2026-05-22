"""Load and save knowlyx.toml workspace config."""

from __future__ import annotations

from pathlib import Path

from knowlyx.workspace.schema import RepoConfig, RepoDependency, RepoRole, WorkspaceConfig

_DEFAULT_FILENAME = "knowlyx.toml"


def load(workspace_path: str | Path = ".") -> WorkspaceConfig:
    """
    Load knowlyx.toml from workspace_path. Returns empty config if not found.

    Resolution order:
    1. If workspace_path/knowlyx.toml exists → load that (legacy/sibling layout)
    2. Else if workspace_path (or ancestor) is a linked repo → load central
       ~/.knowlyx/workspaces/<name>/workspace.toml
    3. Else return empty config named after the folder
    """
    root = Path(workspace_path).resolve()
    toml_file = root / _DEFAULT_FILENAME
    if toml_file.exists():
        return _read_toml(toml_file, root)

    # Try central lookup via link config
    from knowlyx.link.resolver import resolve_workspace
    res = resolve_workspace(workspace_path)
    if res is not None:
        central = res.workspace_dir / "workspace.toml"
        if central.exists():
            return _read_toml(central, res.workspace_dir)

    return WorkspaceConfig(name=root.name)


def load_central(workspace_name: str) -> WorkspaceConfig:
    """Load workspace.toml directly from ~/.knowlyx/workspaces/<name>/."""
    from knowlyx.paths import workspace_dir, workspace_toml_path
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
    """Serialize config to knowlyx.toml."""
    root = Path(workspace_path).resolve()
    toml_file = root / _DEFAULT_FILENAME
    toml_file.write_text(_serialize(config), encoding="utf-8")
    return toml_file


def init(workspace_path: str | Path = ".", name: str = "") -> WorkspaceConfig:
    """Create a minimal knowlyx.toml in workspace_path."""
    root = Path(workspace_path).resolve()
    config = WorkspaceConfig(name=name or root.name)
    save(config, root)
    return config


def register_repo_in_workspace(
    workspace_name: str,
    repo: RepoConfig,
) -> tuple[bool, Path | None]:
    """
    Auto-add or update a repo entry in `~/.knowlyx/workspaces/<name>/workspace.toml`.

    Returns (changed, written_path). `written_path` is None if the workspace
    folder doesn't exist locally (caller should print the clone hint).
    """
    from knowlyx.paths import workspace_dir, workspace_toml_path

    toml_path = workspace_toml_path(workspace_name)
    if not toml_path.exists():
        return False, None

    # Load via the explicit workspace.toml path (not knowlyx.toml) so we read
    # the central topology file the same one we're about to write back to.
    config = _read_toml(toml_path, toml_path.parent)
    # Preserve the workspace name from the toml (don't let load() default it
    # to the folder name, which can be "tutorial-knowlyx-knowledge" instead
    # of just "tutorial").
    if not config.name or config.name == toml_path.parent.name:
        config = WorkspaceConfig(
            name=workspace_name,
            version=config.version,
            description=config.description,
            repos=config.repos,
            dependencies=config.dependencies,
            global_conventions=config.global_conventions,
            metadata=config.metadata,
        )

    existing_idx = next((i for i, r in enumerate(config.repos) if r.name == repo.name), None)
    if existing_idx is not None:
        existing = config.repos[existing_idx]
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
            return False, toml_path
        config.repos[existing_idx] = merged
    else:
        config.repos.append(repo)

    toml_path.write_text(_serialize(config), encoding="utf-8")
    return True, toml_path


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

def _parse(data: dict, root: Path) -> WorkspaceConfig:
    repos = [
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
    for repo in config.repos:
        lines.append("[[repos]]")
        lines.append(f'name = "{repo.name}"')
        if repo.git_url:
            lines.append(f'git_url = "{repo.git_url}"')
        if repo.path:
            lines.append(f'path = "{repo.path}"')
        if repo.role != RepoRole.UNKNOWN:
            lines.append(f'role = "{repo.role.value}"')
        if repo.domains:
            lines.append(f"domains = {repo.domains!r}")
        if repo.tags:
            lines.append(f"tags = {repo.tags!r}")
        if repo.critical:
            lines.append("critical = true")
        if repo.description:
            lines.append(f'description = "{repo.description}"')
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
