"""Precept CLI — cognitive enforcement for AI development."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure unicode output works on Windows consoles that default to cp1252
# (bash from MINGW64, cmd.exe without chcp 65001, etc.). Without this,
# rich's Console blows up trying to render arrows / checkmarks / bullets.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

app = typer.Typer(
    name="precept",
    help="Cognitive enforcement layer for AI software development.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        from precept import __version__
        console.print(f"precept {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Cognitive enforcement layer for AI software development."""


def _load_engine(repo_path: str):
    from precept.graph.cognitive_graph import CognitiveGraph
    from precept.reasoning.engine import ReasoningEngine
    from precept.scanner.repo_scanner import RepoScanner

    _print_workspace_hint(repo_path)
    scanner = RepoScanner(repo_path)
    with console.status("[bold cyan]Scanning repository…"):
        scan = scanner.scan()
    graph = CognitiveGraph()
    graph.build(scan)
    engine = ReasoningEngine(scan, graph)
    return engine, scan, graph


def _resolve_workspace_dir(repo_path: str | Path) -> Path | None:
    """Return the knowledge-home folder for this repo, or None if unresolved.

    Walks up looking for `workspace.toml` (knowledge-home mode), else resolves
    via the link config to the registered workspace path.
    """
    p = Path(repo_path).resolve()
    while True:
        if (p / "workspace.toml").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    try:
        from precept.link.resolver import resolve_workspace
        res = resolve_workspace(repo_path)
        if res is not None and (res.workspace_dir / "workspace.toml").exists():
            return res.workspace_dir
    except Exception:
        pass
    return None


def _auto_sync_workspace(repo_path: str | Path, message: str, files: list[str] | None = None) -> None:
    """Schedule pull → commit → push in a detached background process.

    Returns instantly so the calling CLI command doesn't block on git I/O.
    Failures are written to `<workspace>/.precept-sync-status.json` for
    `precept doctor` to surface.
    """
    try:
        from precept import sync as _sync
        if not _sync.sync_enabled():
            return
        ws = _resolve_workspace_dir(repo_path)
        if ws is None:
            return
        _sync.schedule_full_sync(ws, message=message, files=files)
    except Exception:
        pass  # auto-sync must never block or break a CLI command


def _print_workspace_hint(repo_path: str) -> None:
    """Print a one-line setup hint if the shared knowledge isn't on this machine."""
    try:
        from precept.link.resolver import workspace_setup_hint
        hint = workspace_setup_hint(repo_path)
        if hint:
            console.print(f"[yellow]ℹ {hint}[/yellow]")
    except Exception:
        pass  # never let hint logic break the command


# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------


@app.command()
def scan(
    repo_path: str = typer.Argument(".", help="Path to the repository"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Scan a repository and show its cognitive profile."""
    from precept.scanner.repo_scanner import RepoScanner

    scanner = RepoScanner(repo_path)
    with console.status("[bold cyan]Scanning…"):
        result = scanner.scan()

    if json_output:
        print(result.model_dump_json(indent=2))
        return

    console.print(Panel(
        f"[bold]{Path(repo_path).resolve().name}[/bold]\n"
        f"Language: [cyan]{result.language}[/cyan]  Framework: [cyan]{result.framework}[/cyan]\n"
        f"Architecture: [yellow]{result.architecture.value}[/yellow]\n"
        f"Files: {result.metadata.get('total_files', '?')}  "
        f"Monorepo: {'yes' if result.metadata.get('monorepo') else 'no'}  "
        f"Docker: {'yes' if result.metadata.get('has_docker') else 'no'}",
        title="[bold green]Precept Scan[/bold green]",
    ))

    if result.domains:
        console.print("\n[bold]Detected Domains:[/bold]", ", ".join(f"[cyan]{d}[/cyan]" for d in result.domains))

    if result.api_clients:
        console.print("[bold]API Clients (generated):[/bold]", *result.api_clients)

    if result.conventions:
        t = Table(title="Conventions", show_header=True)
        t.add_column("Name", style="bold")
        t.add_column("Rule")
        t.add_column("Enforced", justify="center")
        for c in result.conventions:
            t.add_row(c.name, c.rule, "[red]✓[/red]" if c.enforced else "○")
        console.print(t)

    if result.forbidden_patterns:
        console.print("\n[bold red]Forbidden Patterns:[/bold red]")
        for p in result.forbidden_patterns:
            console.print(f"  [red]✗[/red] {p}")

    if result.reusable_assets:
        console.print(f"\n[bold green]Reusable Assets:[/bold green] {len(result.reusable_assets)} found")
        by_type: dict[str, list] = {}
        for a in result.reusable_assets:
            by_type.setdefault(a.asset_type, []).append(a)
        for atype, assets in by_type.items():
            console.print(f"  [cyan]{atype}[/cyan]: {', '.join(a.name for a in assets[:5])}" +
                          (f" (+{len(assets)-5} more)" if len(assets) > 5 else ""))


@app.command(name="install-claude-commands")
def install_claude_commands(
    user: bool = typer.Option(True, "--user/--project", help="Install to ~/.claude/commands (user) or ./.claude/commands (project)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
):
    """Install precept's Claude Code slash commands (e.g. /precept-generate).

    Copies the bundled command templates into your Claude Code commands
    directory. After install, type `/precept-generate` in Claude Code to have
    Claude scan the repo and write semantically meaningful memory entries.
    """
    import importlib.resources as _res
    import shutil

    target_dir = Path.home() / ".claude" / "commands" if user else Path.cwd() / ".claude" / "commands"
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        bundle = _res.files("precept.claude_commands")
    except ModuleNotFoundError:
        console.print("[red]precept.claude_commands package not found — reinstall precept.[/red]")
        raise typer.Exit(1)

    copied: list[str] = []
    for entry in bundle.iterdir():
        if entry.name.endswith(".md"):
            target = target_dir / entry.name
            if target.exists() and not force:
                console.print(f"  [yellow]skip[/yellow]  {target} (exists — re-run with --force)")
                continue
            with _res.as_file(entry) as src:
                shutil.copy(src, target)
            copied.append(entry.name)
            console.print(f"  [green]wrote[/green] {target}")

    if copied:
        console.print(f"\n[green]Installed {len(copied)} command(s)[/green] to {target_dir}")
        console.print("Open Claude Code and try [cyan]/precept-generate[/cyan].")
    else:
        console.print(f"\n[yellow]Nothing installed.[/yellow] Re-run with --force to overwrite {target_dir}.")


@app.command()
def analyze(
    request: str = typer.Argument(..., help="User request in natural language"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Path to the repository"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Analyze a request: intent → impact → risk → plan."""
    engine, scan, _ = _load_engine(repo_path)
    with console.status("[bold cyan]Reasoning…"):
        report = engine.analyze(request)

    if json_output:
        print(report.model_dump_json(indent=2))
        return

    # Decision banner
    decision_color = {
        "proceed": "green", "warn": "yellow", "ask": "blue", "reject": "red"
    }[report.risk.decision.value]
    console.print(Panel(
        f"[bold {decision_color}]{report.risk.decision.value.upper()}[/bold {decision_color}] — "
        f"Risk: [bold]{report.risk.level.value.upper()}[/bold]",
        title="[bold]AI Decision[/bold]",
    ))

    # Intent
    console.print(f"\n[bold]Domain:[/bold] [cyan]{report.intent.detected_domain}[/cyan]  "
                  f"[bold]Action:[/bold] [cyan]{report.intent.detected_action}[/cyan]")

    if report.intent.inferred_requirements:
        console.print("\n[bold]Inferred Requirements:[/bold]")
        for r in report.intent.inferred_requirements:
            console.print(f"  • {r}")

    # Impact
    if report.impact.affected_domains:
        console.print(f"\n[bold]Affected Domains:[/bold] {', '.join(f'[yellow]{d}[/yellow]' for d in report.impact.affected_domains)}")
    if report.impact.affected_services:
        console.print(f"[bold]Affected Services:[/bold] {', '.join(report.impact.affected_services)}")
    if report.impact.cascade_risks:
        console.print("\n[bold red]Cascade Risks:[/bold red]")
        for r in report.impact.cascade_risks:
            console.print(f"  [red]⚠[/red] {r}")

    # Warnings
    if report.risk.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in report.risk.warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    # Clarification
    if report.intent.requires_clarification:
        console.print("\n[bold blue]Clarification Needed:[/bold blue]")
        for q in report.intent.clarification_questions:
            console.print(f"  [blue]?[/blue] {q}")

    # Reusable assets
    if report.reusable_assets_to_use:
        console.print("\n[bold green]Reuse Before Creating:[/bold green]")
        for a in report.reusable_assets_to_use[:5]:
            console.print(f"  [green]→[/green] [{a.asset_type}] {a.name} ({a.path})")

    # Plan
    if report.suggested_plan:
        console.print("\n[bold]Suggested Workflow:[/bold]")
        for step in report.suggested_plan:
            console.print(f"  {step}")


@app.command()
def conventions(
    repo_path: str = typer.Argument(".", help="Path to the repository"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """List all detected conventions for the repository."""
    from precept.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner(repo_path)
    with console.status("[bold cyan]Scanning…"):
        result = scanner.scan()

    if json_output:
        print(json.dumps([c.model_dump() for c in result.conventions], indent=2))
        return

    t = Table(title="Repository Conventions", show_header=True)
    t.add_column("Name", style="bold cyan")
    t.add_column("Rule")
    t.add_column("Enforced", justify="center")
    for c in result.conventions:
        t.add_row(c.name, c.rule, "[red]ENFORCED[/red]" if c.enforced else "optional")
    console.print(t)

    if result.forbidden_patterns:
        console.print("\n[bold red]Forbidden Patterns:[/bold red]")
        for p in result.forbidden_patterns:
            console.print(f"  [red]✗[/red] {p}")


@app.command()
def impact(
    change: str = typer.Argument(..., help="Describe the change"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Show the blast radius of a planned change."""
    _, scan, graph = _load_engine(repo_path)
    from precept.reasoning.impact_analyzer import ImpactAnalyzer
    from precept.reasoning.intent_analyzer import IntentAnalyzer

    with console.status("[bold cyan]Analyzing impact…"):
        intent = IntentAnalyzer(scan).analyze(change)
        result = ImpactAnalyzer(scan, graph).analyze(intent)

    if json_output:
        print(result.model_dump_json(indent=2))
        return

    console.print(Panel(
        f"Primary domain: [cyan]{intent.detected_domain}[/cyan]",
        title="[bold]Impact Analysis[/bold]",
    ))
    console.print(f"\n[bold]Affected Domains:[/bold] {', '.join(f'[yellow]{d}[/yellow]' for d in result.affected_domains)}")
    console.print(f"[bold]Affected Services:[/bold] {', '.join(result.affected_services) or 'none detected'}")
    if result.cascade_risks:
        console.print("\n[bold red]Cascade Risks:[/bold red]")
        for r in result.cascade_risks:
            console.print(f"  [red]⚠[/red] {r}")
    if result.affected_files:
        console.print(f"\n[bold]Affected Files:[/bold] ({len(result.affected_files)})")
        for f in result.affected_files[:10]:
            console.print(f"  [{f.impact_type}] {f.path} — {f.reason}")


@app.command()
def assets(
    domain: str = typer.Argument("", help="Filter by domain (optional)"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List reusable assets. Check before creating new code."""
    from precept.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner(repo_path)
    with console.status("[bold cyan]Scanning assets…"):
        result = scanner.scan()

    filtered = [a for a in result.reusable_assets if not domain or domain in a.tags or domain in a.name.lower()]

    if json_output:
        print(json.dumps([a.model_dump() for a in filtered], indent=2))
        return

    t = Table(title=f"Reusable Assets{f' [{domain}]' if domain else ''}", show_header=True)
    t.add_column("Type", style="cyan")
    t.add_column("Name", style="bold")
    t.add_column("Path")
    t.add_column("Tags")
    for a in filtered:
        t.add_row(a.asset_type, a.name, a.path, ", ".join(a.tags))
    console.print(t)


@app.command()
def memory(
    action: str = typer.Argument(..., help="list | recall | decide | forget"),
    query: str = typer.Argument("", help="For decide: domain. For recall: search query. For forget: entry ID."),
    title_arg: str = typer.Argument("", help="For decide: title of the decision."),
    domain: str = typer.Option("", "--domain", "-d"),
    title: str = typer.Option("", "--title"),
    body: str = typer.Option("", "--body"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
):
    """
    Manage Precept memory.

    \b
    precept memory list                        # list all entries
    precept memory recall "payment idempotency"
    precept memory decide payment "Use Redis queue" --body "All async jobs via BullMQ"
    precept memory forget <entry-id>
    """
    from precept.memory.schema import MemoryEntry, MemoryKind
    from precept.memory.store import create_store
    _print_workspace_hint(repo_path)
    store = create_store(repo_path)

    if action == "list":
        entries = store.list_by_domain(domain) if domain else store.all()
        t = Table(title="Memory", show_header=True)
        t.add_column("ID", style="dim", width=18)
        t.add_column("Kind", style="cyan")
        t.add_column("Domain")
        t.add_column("Title")
        t.add_column("Approved", justify="center")
        for e in entries:
            t.add_row(e.id, e.kind.value, e.domain, e.title, "[green]+[/green]" if e.approved else "[yellow]pending[/yellow]")
        console.print(t)

    elif action == "recall":
        results = store.search(query, domain=domain, limit=10)
        approved = [r for r in results if r.approved]
        if not approved:
            console.print("[yellow]No approved memories found.[/yellow]")
            return
        for m in approved:
            console.print(Panel(m.body, title=f"[bold]{m.title}[/bold] [{m.domain}] [{m.kind.value}]"))

    elif action == "decide":
        # Accept title from either the positional `title_arg` or the --title flag.
        resolved_title = title or title_arg
        if not query or not body:
            console.print("[red]Usage:[/red] precept memory decide <domain> \"<title>\" --body \"<decision>\"")
            raise typer.Exit(1)
        entry = MemoryEntry(
            id="",
            kind=MemoryKind.TEAM_DECISION,
            domain=query,
            title=resolved_title or body[:60],
            body=body,
            approved=True,
            approved_by="team",
            repo_path=repo_path,
        )
        saved = store.save(entry)
        console.print(f"[green]Decision saved and approved[/green] — ID: {saved.id}")
        _auto_sync_workspace(repo_path, f"memory({query}): {saved.title[:60]}")

    elif action == "forget":
        if store.delete(query):
            console.print(f"[green]Deleted[/green] {query}")
        else:
            console.print(f"[red]Not found[/red]: {query}")

    else:
        console.print(f"[red]Unknown action: {action}[/red]. Use: list | recall | decide | forget")


@app.command()
def pack(
    domain: str = typer.Argument(..., help="Domain name (auth, payment, webhook, order, otp, notification, worker)"),
):
    """Show the built-in cognition pack for a domain."""
    from precept.packs.builtin import get_pack
    p = get_pack(domain)
    if not p:
        console.print(f"[red]No pack for '{domain}'.[/red] Available: auth, otp, payment, webhook, order, notification, worker")
        raise typer.Exit(1)
    console.print(Panel(p.description, title=f"[bold cyan]Cognition Pack: {p.domain}[/bold cyan]"))
    console.print("\n[bold]Business Rules:[/bold]")
    for r in p.business_rules:
        console.print(f"  • {r}")
    console.print("\n[bold]Common Requirements:[/bold]")
    for r in p.common_requirements:
        console.print(f"  • {r}")
    console.print("\n[bold red]Risk Flags:[/bold red]")
    for r in p.risk_flags:
        console.print(f"  [red]⚠[/red] {r}")
    console.print("\n[bold yellow]Forbidden Shortcuts:[/bold yellow]")
    for r in p.forbidden_shortcuts:
        console.print(f"  [yellow]✗[/yellow] {r}")
    if p.questions_to_ask:
        console.print("\n[bold blue]Questions to clarify:[/bold blue]")
        for q in p.questions_to_ask:
            console.print(f"  [blue]?[/blue] {q}")


@app.command()
def workspace(
    action: str = typer.Argument(..., help="init | create | list | scan | impact | graph | cache"),
    target: str = typer.Argument("", help="Workspace name | repo name | format"),
    change: str = typer.Option("", "--change", "-c", help="Change description (for impact)"),
    workspace_path: str = typer.Option(".", "--workspace", "-w"),
    persist: bool = typer.Option(False, "--persist", help="Save scans into central cache (for scan action)"),
    json_output: bool = typer.Option(False, "--json"),
):
    """
    Multi-repo workspace commands.

    \b
    precept workspace init                        # create precept.toml in cwd (legacy)
    precept workspace create my-product           # create central workspace at ~/.precept/workspaces/
    precept workspace list                        # list all central workspaces
    precept workspace scan                        # scan all repos
    precept workspace impact api -c "rename users.email"
    precept workspace graph                       # print mermaid diagram
    precept workspace graph react_flow --json     # React Flow JSON
    """
    from precept.workspace.config_loader import init, load
    from precept.workspace.multi_scanner import CrossRepoImpactAnalyzer, WorkspaceScanner

    if action == "init":
        cfg = init(workspace_path)
        console.print(f"[green]Created[/green] precept.toml for workspace '{cfg.name}'")
        console.print("Edit precept.toml to add [[repos]] and [[dependencies]] sections.")
        return

    if action == "create":
        if not target:
            console.print("[red]Provide workspace name:[/red] precept workspace create <name>")
            raise typer.Exit(1)
        from precept.paths import ensure_workspace_dir, workspace_toml_path
        from precept.workspace.config_loader import _serialize
        from precept.workspace.schema import WorkspaceConfig
        ws_dir = ensure_workspace_dir(target)
        toml_path = workspace_toml_path(target)
        if toml_path.exists():
            console.print(f"[yellow]Workspace '{target}' already exists[/yellow] at {ws_dir}")
            raise typer.Exit(0)
        toml_path.write_text(_serialize(WorkspaceConfig(name=target)), encoding="utf-8")
        console.print(f"[green]Created central workspace[/green] '{target}'")
        console.print(f"  Path: {ws_dir}")
        console.print(f"  Topology: {toml_path}")
        console.print(f"  Memory: {ws_dir / 'memory.json'}")
        console.print(f"  Approvals: {ws_dir / 'approvals.json'}")
        console.print(f"\nNext: in each repo, run [cyan]precept link {target}[/cyan]")
        return

    if action == "list":
        from precept.paths import list_workspaces, precept_home
        names = list_workspaces()
        if json_output:
            print(json.dumps({"home": str(precept_home()), "workspaces": names}, indent=2))
            return
        console.print(f"[bold]Central workspaces[/bold] at {precept_home()}")
        if not names:
            console.print("  [dim](none — run `precept workspace create <name>` to add one)[/dim]")
            return
        for n in names:
            console.print(f"  • [cyan]{n}[/cyan]")
        return

    config = load(workspace_path)
    if not config.repos and action != "init":
        console.print("[yellow]No repos in precept.toml. Add [[repos]] entries first.[/yellow]")
        raise typer.Exit(1)

    if action == "cache":
        from precept.cache.scan_cache import ScanCache
        from precept.link.resolver import resolve_workspace
        res = resolve_workspace(workspace_path)
        ws_name = res.workspace_name if res else config.name
        cache = ScanCache(ws_name)
        names = cache.list_cached()
        if json_output:
            print(json.dumps([cache.metadata(n) for n in names], indent=2))
            return
        if not names:
            console.print(f"[yellow]No cached scans for workspace '{ws_name}'.[/yellow]")
            console.print("Run [cyan]precept workspace scan --persist[/cyan] on a machine with the repos cloned.")
            return
        t = Table(title=f"Cached scans — {ws_name}", show_header=True)
        t.add_column("Repo", style="bold")
        t.add_column("Cached at")
        for n in names:
            md = cache.metadata(n) or {}
            t.add_row(n, md.get("cached_at", "?"))
        console.print(t)
        return

    if action == "scan":
        scanner = WorkspaceScanner(config, persist_cache=persist)
        with console.status("[bold cyan]Scanning workspace…"):
            ws = scanner.scan()
        summary = ws.summary()
        if json_output:
            print(json.dumps(summary, indent=2))
            return
        console.print(Panel(f"Workspace: [bold]{summary['workspace']}[/bold]  Repos: {len(summary['repos'])}", title="[bold green]Workspace Scan[/bold green]"))
        t = Table(show_header=True)
        t.add_column("Repo", style="bold")
        t.add_column("Role", style="cyan")
        t.add_column("Stack")
        t.add_column("Domains")
        t.add_column("Critical", justify="center")
        for r in summary["repos"]:
            t.add_row(r["name"], r["role"], f"{r['language']}/{r['framework']}", ", ".join(r["domains"][:4]), "[red]✓[/red]" if r["critical"] else "")
        console.print(t)
        if summary.get("errors"):
            console.print("\n[red]Scan errors:[/red]", summary["errors"])

    elif action == "impact":
        if not target:
            console.print("[red]Specify repo name: precept workspace impact <repo-name> --change '...'[/red]")
            raise typer.Exit(1)
        scanner = WorkspaceScanner(config)
        with console.status("[bold cyan]Scanning + analyzing impact…"):
            ws = scanner.scan()
            analyzer = CrossRepoImpactAnalyzer(ws, config)
            result = analyzer.analyze(target, change or "unspecified change")
        if json_output:
            print(json.dumps(result, indent=2))
            return
        console.print(Panel(f"Changed: [bold]{target}[/bold]  Change: {change}", title="[bold]Cross-Repo Impact[/bold]"))
        if result.get("critical_repos_affected"):
            console.print("[bold red]⚠ CRITICAL REPO AFFECTED — human review required[/bold red]")
        console.print(f"\n[bold]Directly affected:[/bold] {', '.join(result.get('directly_affected_repos', []))}")
        console.print(f"[bold]All affected:[/bold] {', '.join(result.get('all_affected_repos', []))}")
        if result.get("per_repo_impact"):
            t = Table(title="Per-repo impact", show_header=True)
            t.add_column("Repo", style="bold")
            t.add_column("Role")
            t.add_column("Relation")
            t.add_column("Reason")
            for r in result["per_repo_impact"]:
                t.add_row(r["repo"], r["role"], r["relation"], r["reason"][:60])
            console.print(t)

    elif action == "graph":
        fmt = target or "mermaid"
        from precept.graph.exporter import GraphExporter
        scanner = WorkspaceScanner(config)
        with console.status("[bold cyan]Scanning workspace…"):
            ws = scanner.scan()
        if fmt == "mermaid":
            mermaid = GraphExporter.workspace_to_mermaid(ws)
            if json_output:
                print(mermaid)
            else:
                console.print(Panel(mermaid, title="[bold]Mermaid Workspace Graph[/bold]"))
        elif fmt == "dot":
            print(GraphExporter.workspace_to_dot(ws))
        elif fmt == "react_flow":
            print(json.dumps(GraphExporter.to_workspace_react_flow(ws), indent=2))
        else:
            console.print(f"[red]Unknown format '{fmt}'[/red]. Use: mermaid | dot | react_flow")
    else:
        console.print(f"[red]Unknown action '{action}'[/red]. Use: init | scan | impact | graph")


@app.command()
def approval(
    action: str = typer.Argument(..., help="list | approve | reject | show"),
    request_id: str = typer.Argument("", help="Approval request ID"),
    reason: str = typer.Option("", "--reason"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    json_output: bool = typer.Option(False, "--json"),
):
    """
    Manage human approval requests.

    \b
    precept approval list              # list pending approvals
    precept approval show <id>         # show details
    precept approval approve <id>
    precept approval reject <id> --reason "too risky right now"
    """
    from precept.approval.queue import get_queue

    queue = get_queue(repo_path)

    if action == "list":
        entries = queue.pending()
        if json_output:
            print(json.dumps([r.model_dump(mode="json") for r in entries], indent=2, default=str))
            return
        if not entries:
            console.print("[green]No pending approvals.[/green]")
            return
        t = Table(title="Pending Approvals", show_header=True)
        t.add_column("ID", style="dim")
        t.add_column("Title", style="bold")
        t.add_column("Domain", style="cyan")
        t.add_column("Risk")
        for r in entries:
            risk_color = {"critical": "red", "high": "yellow", "medium": "blue"}.get(r.risk_level, "white")
            t.add_row(r.id, r.title, r.domain, f"[{risk_color}]{r.risk_level}[/{risk_color}]")
        console.print(t)

    elif action == "show":
        if not request_id:
            console.print("[red]Provide a request ID.[/red]")
            raise typer.Exit(1)
        req = queue.get(request_id)
        if not req:
            console.print(f"[red]Not found:[/red] {request_id}")
            raise typer.Exit(1)
        console.print(Panel(
            f"[bold]Title:[/bold] {req.title}\n"
            f"[bold]Domain:[/bold] {req.domain}  [bold]Risk:[/bold] {req.risk_level}\n"
            f"[bold]Action:[/bold] {req.requested_action}\n\n"
            f"{req.description}",
            title=f"[bold]Approval Request — {req.status.value.upper()}[/bold]",
        ))
        if req.impact_summary:
            console.print("[bold]Impact:[/bold]", *[f"\n  • {i}" for i in req.impact_summary])
        if req.warnings:
            console.print("[bold yellow]Warnings:[/bold yellow]", *[f"\n  [yellow]![/yellow] {w}" for w in req.warnings])

    elif action == "approve":
        if not request_id:
            console.print("[red]Provide a request ID.[/red]")
            raise typer.Exit(1)
        req = queue.approve(request_id)
        if not req:
            console.print(f"[red]Not found:[/red] {request_id}")
            raise typer.Exit(1)
        console.print(f"[green]Approved[/green] — {req.title}")
        _auto_sync_workspace(repo_path, f"approval: approved {request_id[:8]}")

    elif action == "reject":
        if not request_id:
            console.print("[red]Provide a request ID.[/red]")
            raise typer.Exit(1)
        req = queue.reject(request_id, reason)
        if not req:
            console.print(f"[red]Not found:[/red] {request_id}")
            raise typer.Exit(1)
        console.print(f"[red]Rejected[/red] — {req.title}" + (f" ({reason})" if reason else ""))
        _auto_sync_workspace(repo_path, f"approval: rejected {request_id[:8]}")
    else:
        console.print(f"[red]Unknown action '{action}'[/red]. Use: list | show | approve | reject")


@app.command()
def graph(
    format: str = typer.Argument("mermaid", help="mermaid | dot | react_flow"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
):
    """Export the cognitive graph for a single repo."""
    from precept.graph.cognitive_graph import CognitiveGraph
    from precept.graph.exporter import GraphExporter
    from precept.scanner.repo_scanner import RepoScanner

    scanner = RepoScanner(repo_path)
    with console.status("[bold cyan]Scanning…"):
        scan_result = scanner.scan()
    g = CognitiveGraph()
    g.build(scan_result)

    if format == "mermaid":
        console.print(GraphExporter.to_mermaid(g))
    elif format == "dot":
        print(GraphExporter.to_dot(g))
    elif format == "react_flow":
        print(json.dumps(GraphExporter.to_react_flow(g), indent=2))
    else:
        console.print(f"[red]Unknown format '{format}'[/red]. Use: mermaid | dot | react_flow")


@app.command()
def link(
    workspace_name: str = typer.Argument(..., help="Central workspace to link this repo to"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    repo_name: str = typer.Option("", "--name", help="Override repo name (defaults to folder name)"),
    role: str = typer.Option("unknown", "--role", help="backend | frontend | worker | gateway | shared | infra"),
    domains: str = typer.Option("", "--domains", help="Comma-separated domains"),
    critical: bool = typer.Option(False, "--critical", help="Mark as critical repo"),
    remote: str = typer.Option("", "--remote", help="Git URL of the shared knowledge repo (e.g. git@github.com:org/x-knowledge.git)"),
):
    """
    Link this repo to a central workspace so memory + approvals + topology are shared.

    \b
    precept link my-product --role backend --domains billing,auth --critical \\
                            --remote git@github.com:org/my-product-knowledge.git
    """
    from precept.link.config import LinkConfig, save_link
    from precept.paths import workspace_dir, workspace_toml_path

    ws_exists_locally = workspace_toml_path(workspace_name).exists()
    if not ws_exists_locally and not remote:
        console.print(f"[red]Workspace '{workspace_name}' does not exist locally and no --remote provided.[/red]")
        console.print(f"Either: [cyan]precept workspace create {workspace_name}[/cyan]")
        console.print(f"Or:     [cyan]precept link {workspace_name} --remote <git-url>[/cyan]  (clone shared knowledge)")
        raise typer.Exit(1)

    cfg = LinkConfig(
        workspace=workspace_name,
        repo_name=repo_name,
        role=role,
        domains=[d.strip() for d in domains.split(",") if d.strip()],
        critical=critical,
        knowledge_remote=remote,
    )
    written = save_link(cfg, repo_path)
    console.print(f"[green]Linked[/green] {Path(repo_path).resolve().name} → workspace '{workspace_name}'")
    console.print(f"  Config: {written}  [dim](commit this to git)[/dim]")
    console.print(f"  Shared store: {workspace_dir(workspace_name)}")
    if remote:
        console.print(f"  Knowledge remote: {remote}")
    if not ws_exists_locally and remote:
        console.print(
            f"\n[yellow]⚠ Shared knowledge not on this machine yet.[/yellow]\n"
            f"  Run:  [cyan]git clone {remote} {workspace_dir(workspace_name)}[/cyan]"
        )


@app.command()
def unlink(
    repo_path: str = typer.Option(".", "--repo", "-r"),
):
    """Remove this repo's link to a central workspace.

    If precept.config also carries a [database] section, only the link fields
    are stripped; the file (and DB credentials) stay. Otherwise the whole
    file is deleted.
    """
    from precept.link.config import _extract_database_section
    from precept.paths import repo_link_config_path

    path = repo_link_config_path(repo_path)
    if not path.exists():
        console.print("[yellow]No link config found.[/yellow]")
        raise typer.Exit(0)
    db_section = _extract_database_section(path)
    if db_section:
        path.write_text(db_section, encoding="utf-8")
        console.print(f"[green]Unlinked[/green] (kept [database] in {path})")
    else:
        path.unlink()
        console.print(f"[green]Unlinked[/green] {path}")


@app.command()
def migrate(
    repo_path: str = typer.Option(".", "--repo", "-r"),
    workspace_name: str = typer.Option("", "--workspace", "-w", help="Target workspace (must exist)"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """
    Migrate legacy per-repo .precept/{memory,approvals}.json into a central workspace.

    \b
    1. precept workspace create my-product
    2. precept link my-product --repo /path/to/api
    3. precept migrate --repo /path/to/api
    """
    import json as _json

    from precept.link.config import load_link
    from precept.paths import workspace_approvals_path, workspace_memory_path

    legacy_dir = Path(repo_path) / ".precept"
    legacy_memory = legacy_dir / "memory.json"
    legacy_approvals = legacy_dir / "approvals.json"

    if not legacy_memory.exists() and not legacy_approvals.exists():
        console.print("[yellow]Nothing to migrate.[/yellow] No legacy .precept/memory.json or approvals.json found.")
        raise typer.Exit(0)

    if not workspace_name:
        link = load_link(repo_path)
        if not link:
            console.print("[red]No workspace specified and no link config found.[/red]")
            console.print("Either pass --workspace <name> or run `precept link <name>` first.")
            raise typer.Exit(1)
        workspace_name = link.workspace

    target_memory = workspace_memory_path(workspace_name)
    target_approvals = workspace_approvals_path(workspace_name)

    moved_memory = 0
    moved_approvals = 0

    if legacy_memory.exists():
        src = _json.loads(legacy_memory.read_text(encoding="utf-8") or "{}")
        dst = _json.loads(target_memory.read_text(encoding="utf-8")) if target_memory.exists() else {}
        # merge: existing target wins on id collision (safer)
        for k, v in src.items():
            if k not in dst:
                dst[k] = v
                moved_memory += 1
        if not dry_run:
            target_memory.parent.mkdir(parents=True, exist_ok=True)
            target_memory.write_text(_json.dumps(dst, indent=2, default=str), encoding="utf-8")

    if legacy_approvals.exists():
        src = _json.loads(legacy_approvals.read_text(encoding="utf-8") or "{}")
        dst = _json.loads(target_approvals.read_text(encoding="utf-8")) if target_approvals.exists() else {}
        for k, v in src.items():
            if k not in dst:
                dst[k] = v
                moved_approvals += 1
        if not dry_run:
            target_approvals.parent.mkdir(parents=True, exist_ok=True)
            target_approvals.write_text(_json.dumps(dst, indent=2, default=str), encoding="utf-8")

    verb = "Would migrate" if dry_run else "Migrated"
    console.print(f"[green]{verb}[/green] {moved_memory} memory entries → {target_memory}")
    console.print(f"[green]{verb}[/green] {moved_approvals} approval entries → {target_approvals}")
    if not dry_run:
        console.print(f"\n[dim]Original files preserved at {legacy_dir}. Delete manually when satisfied.[/dim]")


@app.command()
def init(
    repo_path: str = typer.Option(".", "--repo", "-r"),
    workspace_mode: bool = typer.Option(False, "--workspace", help="Legacy: create precept.toml in cwd"),
    name: str = typer.Option("", "--name", help="Workspace name (overrides auto-detection)"),
    link_to: str = typer.Option("", "--link", help="Force link mode to a specific workspace name"),
    remote: str = typer.Option("", "--remote", help="Git URL of shared knowledge repo (overrides auto-detection)"),
    knowledge: bool = typer.Option(False, "--knowledge", help="Force knowledge-home mode (set up this folder as the workspace home)"),
):
    """
    Set up Precept in this folder. Auto-detects whether this is a knowledge repo
    or a working repo, and does the right thing.

    \b
    Common usage — just run with no flags:
      cd tutorial-precept-knowledge && precept init   # becomes the workspace home
      cd tutorial-precept-service   && precept init   # auto-links to sibling knowledge repo
      cd tutorial-precept-website   && precept init   # auto-links too

    \b
    Explicit flags (override auto-detection):
      precept init --knowledge --name tutorial        # force knowledge home, custom name
      precept init --link tutorial --remote <git-url> # force link mode with explicit name
      precept init --workspace                        # legacy: write precept.toml (single-repo)
    """
    target = Path(repo_path).resolve()

    # Legacy single-file workspace mode
    if workspace_mode:
        from precept.workspace.config_loader import init as ws_init
        cfg = ws_init(target, name=name)
        console.print(f"[green]Created[/green] precept.toml for workspace '{cfg.name}'")
        console.print("Add [[repos]] and [[dependencies]] sections to precept.toml.")
        return

    # Detect mode in priority order:
    #   1. explicit --link wins
    #   2. explicit --knowledge wins
    #   3. has workspace.toml already → knowledge mode (re-sync)
    #   4. folder name looks like a knowledge repo → knowledge mode
    #   5. sibling *-knowledge folder exists → link mode
    #   6. fall back to scan + suggest
    if link_to:
        _init_link_mode(target, workspace_name=link_to, remote=remote)
        return

    if knowledge or (target / "workspace.toml").exists() or _looks_like_knowledge_repo(target.name):
        _init_knowledge_mode(target, override_name=name)
        return

    sibling = _find_knowledge_sibling(target)
    if sibling is not None:
        _init_link_mode(target, workspace_name="", remote=remote, sibling=sibling)
        return

    _init_suggest(target, name)


def _looks_like_knowledge_repo(folder_name: str) -> bool:
    n = folder_name.lower()
    return n.endswith("-knowledge") or n.endswith("_knowledge") or n == "knowledge"


def _derive_workspace_name(folder_name: str) -> str:
    """
    Strip common project-suffix conventions to derive a clean workspace name.

    Examples:
      tutorial-precept-knowledge → tutorial
      myapp-knowledge            → myapp
      acme_knowledge             → acme
      knowledge                  → knowledge  (no change)
    """
    n = folder_name
    lowered = n.lower()
    for suf in ("-knowledge", "_knowledge"):
        if lowered.endswith(suf) and len(n) > len(suf):
            n = n[: -len(suf)]
            lowered = n.lower()
            break
    for suf in ("-precept", "_precept"):
        if lowered.endswith(suf) and len(n) > len(suf):
            n = n[: -len(suf)]
            break
    return n or folder_name


def _find_knowledge_sibling(target: Path) -> Path | None:
    """Look for a sibling folder that looks like a knowledge repo. None if 0 or >1 found."""
    parent = target.parent
    if not parent.exists() or parent == target:
        return None
    matches = [
        p for p in parent.iterdir()
        if p.is_dir() and p != target and _looks_like_knowledge_repo(p.name)
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _init_knowledge_mode(target: Path, override_name: str = "") -> None:
    """Set up `target` as the workspace home — create workspace files in place and register the path."""
    from precept.paths import ensure_workspace_dir
    from precept.registry import register
    from precept.workspace.config_loader import _serialize, load
    from precept.workspace.schema import WorkspaceConfig

    ws_name = override_name or _derive_workspace_name(target.name)
    toml_path = target / "workspace.toml"

    if toml_path.exists():
        existing = load(target)
        ws_name = override_name or existing.name or ws_name
        register(ws_name, target)
        ensure_workspace_dir(ws_name, at=target)
        console.print(f"[green]Refreshed workspace home[/green] '{ws_name}' at {target}")
        console.print(f"  Registered in: [cyan]{_registry_display_path()}[/cyan]")
        _print_knowledge_next_steps(target)
        return

    ensure_workspace_dir(ws_name, at=target)
    toml_path.write_text(_serialize(WorkspaceConfig(name=ws_name)), encoding="utf-8")
    register(ws_name, target)
    _write_skills_starter(target / "skills")
    _write_getting_started(target, ws_name)

    console.print(f"[green]Created workspace home[/green] '{ws_name}' at {target}")
    console.print("  [green]+[/green] workspace.toml")
    console.print("  [green]+[/green] skills/             (team-authored knowledge — see skills/README.md)")
    console.print("  [green]+[/green] GETTING_STARTED.md  (read this first — full next-step guide)")
    console.print("  [dim]memory.json    (created on first decision)[/dim]")
    console.print("  [dim]approvals.json (created on first approval)[/dim]")
    console.print(f"  Registered in: [cyan]{_registry_display_path()}[/cyan]")
    if override_name == "":
        console.print("  [dim](workspace name derived from folder; override with --name)[/dim]")
    # If this knowledge repo already has a git remote, push the freshly
    # initialized workspace files so teammates can clone immediately.
    _auto_sync_workspace(target, f"chore: init precept workspace '{ws_name}'")
    _print_knowledge_next_steps(target)


def _write_skills_starter(skills_dir: Path) -> None:
    """Drop a README into skills/ on first init so authors see the format."""
    skills_dir.mkdir(parents=True, exist_ok=True)
    readme = skills_dir / "README.md"
    if readme.exists():
        return
    readme.write_text(
        '''# Skills — team-authored knowledge

Drop `<name>.md` files here. Each file is a "skill" — a piece of knowledge
the AI should consult when working in a related area (UI style, money
formatting, deploy quirks, anything that isn't obvious from the code).

## File format

```markdown
---
name: ui-style
description: Use when building or editing UI components — covers Tailwind, design tokens, and shared components.
tags: [ui, frontend]
---

# UI Style Guide

- Use Tailwind v4 utility classes; no inline `style={}`
- Money: format as `THB X,XXX.XX`
- All buttons must use `<Button>` from `src/components/ui/Button.tsx`
- Dark mode: respect `prefers-color-scheme`
```

## How the AI uses them

1. `analyze_intent` returns `available_skills` (every skill's name + description)
2. The AI scans descriptions and calls `read_skill(name)` on anything relevant
3. The AI follows the skill's guidance when writing code

## Authoring tips

- Keep descriptions specific — they're how the AI decides relevance
- Body is free markdown — lists, code blocks, examples all welcome
- Commit + push: skills live in the knowledge repo and sync with the team
''',
        encoding="utf-8",
    )


def _print_knowledge_next_steps(target: Path) -> None:
    git_url = _detect_git_remote(target)
    console.print("\n[bold]Next steps:[/bold]")
    console.print(
        "  [bold]1.[/bold] Read [cyan]GETTING_STARTED.md[/cyan] — full walkthrough lives in this folder."
    )
    if not git_url:
        console.print(
            "  [bold]2.[/bold] Push this folder to GitHub so teammates can clone it:"
        )
        console.print(
            "       [dim]git add . && git commit -m \"chore: init precept workspace\" && git push -u origin main[/dim]"
        )
    else:
        console.print(
            "  [bold]2.[/bold] Commit + push so teammates get it:"
        )
        console.print(
            "       [dim]git add . && git commit -m \"chore: init precept workspace\" && git push[/dim]"
        )
    console.print(
        "  [bold]3.[/bold] In each working repo (sibling folder), run [cyan]precept init[/cyan] —"
    )
    console.print(
        "       it auto-detects this knowledge home and links automatically."
    )


def _write_getting_started(target: Path, ws_name: str) -> None:
    """Drop GETTING_STARTED.md at the workspace root on first init."""
    path = target / "GETTING_STARTED.md"
    if path.exists():
        return
    path.write_text(
        f"""# Precept workspace `{ws_name}` — quick start

This folder is the team's **shared brain**. Anything saved here syncs to git
automatically. Devs talk to Claude — nobody types git or precept commands.

## For each dev (one-time setup per repo)

```bash
cd <my-working-repo>          # sibling of this knowledge folder
precept init                  # auto-links + bootstraps a starter skill from your code
claude mcp add precept -- uvx precept mcp --repo .
```

Done. Open Claude Code / Cursor and start coding.

## Day-to-day

Just talk to Claude. When the conversation produces a team rule, decision, or
convention, Claude saves it for you:

- "We use Stripe only" → `remember_team_decision('billing', ...)` → auto-pushed
- "Money is rendered as THB X,XXX.XX" → `save_skill('ui-money', ...)` → auto-pushed
- "This needs approval" → `request_approval(...)` → auto-pushed

Other devs' Claude sees these on their next request (background pull every ~10s).

## What's in this folder

- `workspace.toml` — topology header (name/version/description)
- `repos/<name>.toml` — one file per linked repo (auto-managed)
- `skills/*.md` — team knowledge (auto-generated `repo-*.md` are starter
  skills from each linked repo's scan — curate them)
- `memory/entries/<id>.json` — decisions (one file per entry, no conflicts)
- `memory/syntheses/<domain>.json` — cached domain summaries
- `approvals/<id>.json` — approval audit trail

All file-per-entry → concurrent writes from 10+ devs never collide.

## If something looks off

```bash
precept doctor                # health check this repo + workspace
precept audit                 # what MCP tools did Claude actually call?
precept sync                  # force a pull+push right now
```

## Opting out of auto-sync (rare)

Set `PRECEPT_AUTO_SYNC=0` in your shell to disable background git. You'll
have to `precept sync` manually.
""",
        encoding="utf-8",
    )


def _bootstrap_starter_skill(
    ws_dir: Path,
    repo_name: str,
    scan,
    role: str,
    domains: list[str],
    git_url: str,
) -> Path | None:
    """
    Write a starter skill summarizing a newly-linked working repo so the team
    has usable knowledge from day 1 — even on an existing/legacy codebase.

    Only writes if the skill doesn't already exist (idempotent). Returns the
    path written, or None if nothing was written.
    """
    skills_dir = ws_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in repo_name).strip("-").lower()
    skill_file = skills_dir / f"repo-{safe}.md"
    if skill_file.exists():
        return None

    language = (getattr(scan, "language", "") or "").strip()
    framework = (getattr(scan, "framework", "") or "").strip()
    architecture = getattr(getattr(scan, "architecture", None), "value", "") or ""
    conventions = list(getattr(scan, "conventions", []) or [])
    forbidden = list(getattr(scan, "forbidden_patterns", []) or [])
    assets = list(getattr(scan, "reusable_assets", []) or [])

    lines: list[str] = []
    lines.append("---")
    lines.append(f"name: repo-{safe}")
    desc = (
        f"Use when working on the {repo_name} repo "
        f"({role}{', ' + framework if framework else ''}). "
        f"Covers its stack, conventions, and reusable assets."
    )
    lines.append(f"description: {desc}")
    tag_list = [t for t in [role, language.lower(), framework.lower(), *domains[:3]] if t]
    if tag_list:
        lines.append("tags: [" + ", ".join(f'"{t}"' for t in tag_list) + "]")
    lines.append("auto_generated: true")
    lines.append("---")
    lines.append("")
    lines.append(f"# `{repo_name}` — auto-detected stack & conventions")
    lines.append("")
    lines.append(
        "_This skill was generated by `precept init` from a static scan. "
        "Curate it as the team learns more — Precept will not overwrite it._"
    )
    lines.append("")

    lines.append("## Stack")
    if language:
        lines.append(f"- **Language:** {language}")
    if framework:
        lines.append(f"- **Framework:** {framework}")
    if architecture:
        lines.append(f"- **Architecture:** {architecture}")
    if role:
        lines.append(f"- **Role:** {role}")
    if git_url:
        lines.append(f"- **Git:** {git_url}")
    lines.append("")

    if domains:
        lines.append("## Detected domains")
        for d in domains:
            lines.append(f"- {d}")
        lines.append("")

    if conventions:
        lines.append("## Conventions (auto-detected)")
        for c in conventions[:10]:
            name = getattr(c, "name", "") or ""
            rule = getattr(c, "rule", "") or ""
            if name and rule:
                lines.append(f"- **{name}** — {rule}")
            elif rule:
                lines.append(f"- {rule}")
        lines.append("")

    if forbidden:
        lines.append("## Forbidden patterns")
        for f in forbidden[:8]:
            lines.append(f"- {f}")
        lines.append("")

    if assets:
        lines.append("## Reusable assets to import (don't recreate)")
        seen: set[str] = set()
        for a in assets[:12]:
            key = f"{getattr(a, 'name', '')}@{getattr(a, 'path', '')}"
            if key in seen:
                continue
            seen.add(key)
            a_type = getattr(a, "asset_type", "")
            a_name = getattr(a, "name", "")
            a_path = getattr(a, "path", "")
            lines.append(f"- `{a_name}` ({a_type}) — `{a_path}`")
        lines.append("")

    lines.append("## How AI should use this")
    lines.append("- Honor every convention above when generating or editing code.")
    lines.append("- Prefer the reusable assets — never recreate one.")
    lines.append("- Treat forbidden patterns as hard blockers in `validate_generated_code`.")
    lines.append("")

    skill_file.write_text("\n".join(lines), encoding="utf-8")
    return skill_file


def _init_link_mode(
    target: Path,
    workspace_name: str,
    remote: str,
    sibling: Path | None = None,
) -> None:
    """Link `target` (a working repo) to a workspace. Either via explicit name or via a knowledge sibling."""
    from precept.link.config import LinkConfig, save_link
    from precept.paths import workspace_dir, workspace_toml_path
    from precept.registry import register
    from precept.scanner.repo_scanner import RepoScanner
    from precept.workspace.config_loader import register_repo_in_workspace
    from precept.workspace.schema import RepoConfig, RepoRole

    # If a sibling knowledge repo was auto-detected, derive name + remote from it.
    if sibling is not None:
        workspace_name = workspace_name or _derive_workspace_name(sibling.name)
        sibling_remote = _detect_git_remote(sibling)
        if not remote:
            remote = sibling_remote
        register(workspace_name, sibling)
        console.print(f"[dim]Auto-detected knowledge sibling: {sibling}[/dim]")
        console.print(f"[dim]Workspace name: {workspace_name}[/dim]")

    if not workspace_name:
        console.print("[red]Could not determine workspace name. Pass --link <name>.[/red]")
        raise typer.Exit(1)

    ws_exists_locally = workspace_toml_path(workspace_name).exists()
    if not ws_exists_locally and not remote and sibling is None:
        console.print(f"[red]Workspace '{workspace_name}' not found locally and no --remote provided.[/red]")
        console.print("Either: [cyan]precept init --knowledge[/cyan] in the knowledge repo first,")
        console.print(f"Or:     [cyan]precept init --link {workspace_name} --remote <git-url>[/cyan]")
        raise typer.Exit(1)

    with console.status("[bold cyan]Auto-detecting role + domains…"):
        scan = RepoScanner(target).scan()
    inferred_role = _infer_role(scan.framework, scan.language)
    inferred_domains = scan.domains[:6]
    repo_git_url = _detect_git_remote(target)

    save_link(LinkConfig(
        workspace=workspace_name,
        knowledge_remote=remote,
    ), target)
    console.print(f"[green]Linked[/green] {target.name} → {workspace_name}")
    console.print(f"  Detected role: [cyan]{inferred_role}[/cyan]  Domains: {', '.join(inferred_domains) or '(none)'}")
    console.print("  Wrote: [cyan]precept.config[/cyan]")
    if repo_git_url:
        console.print(f"  Repo git URL: {repo_git_url}")
    if remote:
        console.print(f"  Knowledge remote: {remote}")

    if ws_exists_locally:
        changed, written = register_repo_in_workspace(
            workspace_name,
            RepoConfig(
                name=target.name,
                git_url=repo_git_url,
                role=RepoRole(inferred_role) if inferred_role in [r.value for r in RepoRole] else RepoRole.UNKNOWN,
                domains=inferred_domains,
            ),
        )
        if written and changed:
            console.print(f"\n[green]+[/green] Auto-registered in workspace.toml: {written}")
            # Push the new repo file up so teammates immediately see the topology.
            _auto_sync_workspace(written.parent.parent, f"topology: register {target.name}")
            # Bootstrap a starter skill from the scan so existing projects
            # land with usable knowledge from day 1.
            ws_dir = written.parent.parent
            skill_path = _bootstrap_starter_skill(
                ws_dir=ws_dir,
                repo_name=target.name,
                scan=scan,
                role=inferred_role,
                domains=inferred_domains,
                git_url=repo_git_url,
            )
            if skill_path is not None:
                console.print(f"  [green]+[/green] Bootstrapped starter skill: [cyan]skills/{skill_path.name}[/cyan]  [dim](edit to refine)[/dim]")
                _auto_sync_workspace(ws_dir, f"skills: bootstrap {skill_path.stem}")
        elif written:
            console.print(f"\n[dim]Repo already registered in {written}, no change.[/dim]")
    elif remote:
        target_path = workspace_dir(workspace_name)
        console.print(
            f"\n[yellow]⚠ Shared knowledge not on this machine yet.[/yellow]\n"
            f"  Run:  [cyan]git clone {remote} {target_path}[/cyan]\n"
            f"  Then re-run [cyan]precept init[/cyan] to auto-register."
        )

    _print_link_next_steps(workspace_name)


def _print_link_next_steps(workspace_name: str) -> None:
    """Print concrete commands to run after linking a working repo."""
    console.print("\n[bold]Next steps:[/bold]")
    console.print(
        "  [bold]1.[/bold] Register Precept as an MCP server in this repo:"
    )
    console.print(
        "       [dim]claude mcp add precept -- uvx precept mcp --repo .[/dim]"
    )
    console.print(
        "  [bold]2.[/bold] In Claude Code, prompt as usual. Claude will call [cyan]analyze_intent[/cyan]"
    )
    console.print(
        "       and discover skills/decisions from the workspace automatically."
    )
    console.print(
        "  [bold]3.[/bold] After Claude runs, verify it actually used Precept:"
    )
    console.print(
        "       [dim]precept audit[/dim]"
    )
    console.print(
        f"  [dim]Workspace knowledge: see ../{Path(_workspace_home_path(workspace_name)).name}/GETTING_STARTED.md[/dim]"
    )


def _workspace_home_path(workspace_name: str) -> str:
    """Return a display-friendly path to the workspace home folder."""
    try:
        from precept.paths import workspace_dir
        return str(workspace_dir(workspace_name))
    except Exception:
        return workspace_name


def _init_suggest(target: Path, name: str) -> None:
    from precept.scanner.repo_scanner import RepoScanner

    with console.status("[bold cyan]Scanning repo…"):
        scan = RepoScanner(target).scan()
    role = _infer_role(scan.framework, scan.language)
    console.print(Panel(
        f"[bold]Folder:[/bold] {target.name}\n"
        f"[bold]Stack:[/bold] {scan.language} / {scan.framework}\n"
        f"[bold]Architecture:[/bold] {scan.architecture.value}\n"
        f"[bold]Suggested role:[/bold] [cyan]{role}[/cyan]\n"
        f"[bold]Detected domains:[/bold] {', '.join(scan.domains) or '(none)'}",
        title="[bold green]Precept Init[/bold green]",
    ))
    suggested = name or target.name
    console.print("\n[bold]No knowledge repo detected nearby.[/bold] Pick one:\n")
    console.print("  [bold]A.[/bold] This repo IS the knowledge home (tech-lead setup):")
    console.print(f"     [cyan]precept init --knowledge --name {suggested}[/cyan]\n")
    console.print("  [bold]B.[/bold] Link to an existing workspace by name:")
    console.print(f"     [cyan]precept init --link {suggested} --remote <git-url>[/cyan]\n")
    console.print("  [bold]C.[/bold] Clone the team's knowledge repo as a sibling first, then re-run [cyan]precept init[/cyan].\n")
    console.print("  [bold]MCP:[/bold] add precept to .claude/settings.json:")
    console.print('     [dim]{"mcpServers": {"precept": {"command": "uvx", "args": ["precept", "mcp", "--repo", "."]}}}[/dim]')


def _registry_display_path() -> str:
    from precept.paths import precept_home
    return str(precept_home() / "registry.toml")


def _detect_git_remote(repo_path: Path) -> str:
    """Best-effort: read `git remote get-url origin` from the repo. Empty on failure."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def _infer_role(framework: str, language: str) -> str:
    fw = (framework or "").lower()
    lg = (language or "").lower()
    if any(k in fw for k in ("next", "react", "vue", "svelte", "angular", "remix", "nuxt")):
        return "frontend"
    if any(k in fw for k in ("fastapi", "django", "flask", "nestjs", "express", "spring", "rails", "gin", "fiber")):
        return "backend"
    if any(k in fw for k in ("celery", "bullmq", "sidekiq")):
        return "worker"
    if lg in ("typescript", "javascript"):
        return "frontend"
    return "backend"


@app.command()
def doctor(
    repo_path: str = typer.Option(".", "--repo", "-r"),
    json_output: bool = typer.Option(False, "--json"),
):
    """
    Diagnose your Precept setup — does each piece work end-to-end?

    Checks (in order):

    \b
    1. Is this folder a Precept workspace home, a linked working repo, or neither?
    2. Does the registry point at a real workspace path?
    3. Is the MCP server reachable via `claude mcp list`? (skipped if `claude` not installed)
    4. How many skills / memory entries are visible to AI?
    5. Are there pending approvals waiting on a human?
    6. Is the last cognition stamp recent enough for commit-check?
    """
    import subprocess
    from datetime import datetime, timezone

    target = Path(repo_path).resolve()
    results: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str, fix: str = "") -> None:
        results.append({"check": name, "status": status, "detail": detail, "fix": fix})

    # 1. Mode detection
    has_workspace_toml = (target / "workspace.toml").exists()
    has_link = (target / ".precept" / "config.toml").exists()
    sibling = _find_knowledge_sibling(target)

    if has_workspace_toml:
        add("mode", "ok", "Knowledge home (workspace.toml present in this folder)")
    elif has_link:
        from precept.link.config import load_link
        link = load_link(target)
        ws_name = link.workspace if link else "?"
        add("mode", "ok", f"Linked working repo → workspace '{ws_name}'")
    elif sibling is not None:
        add("mode", "warn", f"Unlinked but sibling knowledge repo detected: {sibling.name}",
            "Run `precept init` to auto-link.")
    else:
        add("mode", "fail", "Not a Precept folder — no workspace.toml here, no link config, no knowledge sibling",
            "Run `precept init` in a knowledge repo first, then in each working repo.")

    # 2. Workspace resolution + registry health
    from precept.link.resolver import resolve_workspace
    from precept.registry import get_path as get_registered_path
    res = resolve_workspace(target)
    if res is not None:
        ws_name = res.workspace_name
        registered = get_registered_path(ws_name)
        actual_dir = res.workspace_dir
        if not actual_dir.exists() or not (actual_dir / "workspace.toml").exists():
            add("workspace_dir", "fail",
                f"Workspace '{ws_name}' resolves to {actual_dir} but no workspace.toml there",
                "Clone the team's knowledge repo, then `precept init` again.")
        elif registered and registered != actual_dir:
            add("workspace_dir", "warn",
                f"Registry → {registered}\n     Resolved → {actual_dir} (mismatch)",
                "Re-run `precept init` in the knowledge repo to refresh the registry.")
        else:
            add("workspace_dir", "ok", f"Workspace '{ws_name}' at {actual_dir}")
    elif has_workspace_toml:
        # Knowledge mode but no link — check own workspace
        add("workspace_dir", "ok", f"Workspace home at {target}")

    # 3. MCP integration (best-effort, skipped if `claude` not on PATH).
    # shutil.which resolves PATHEXT so Windows finds claude.cmd from npm.
    try:
        claude_exe = shutil.which("claude")
        if claude_exe is None:
            raise FileNotFoundError("claude")
        proc = subprocess.run(
            [claude_exe, "mcp", "list"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if proc.returncode == 0 and "precept" in proc.stdout.lower():
            add("mcp", "ok", "precept registered with Claude Code (`claude mcp list`)")
        elif proc.returncode == 0:
            add("mcp", "warn", "Claude Code MCP list does not include precept",
                "Run: claude mcp add precept -- uvx precept mcp --repo .")
        else:
            add("mcp", "warn", "`claude mcp list` returned non-zero",
                "Check that Claude Code CLI is installed and authenticated.")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        add("mcp", "skip", "`claude` CLI not on PATH — skipping MCP check")

    # 4. Content visibility (skills + memory entries)
    if res is not None or has_workspace_toml:
        from precept.skills import load_workspace_skills
        ws_name = res.workspace_name if res else _derive_workspace_name(target.name)
        try:
            skills = load_workspace_skills(ws_name)
            add("skills", "ok" if skills else "warn",
                f"{len(skills)} skill(s) available" if skills else "No skills authored yet",
                "" if skills else "Drop a `skills/<name>.md` file. See `skills/README.md` for format.")
        except Exception as e:
            add("skills", "warn", f"Could not load skills: {e}")

        try:
            from precept.memory.store import create_store
            store = create_store(str(target))
            entries = store.all()
            approved = [e for e in entries if e.approved]
            add("memory", "ok",
                f"{len(approved)}/{len(entries)} approved memory entries")
        except Exception as e:
            add("memory", "warn", f"Could not read memory store: {e}")

    # 5. Pending approvals
    try:
        from precept.approval.queue import get_queue
        queue = get_queue(str(target))
        pend = queue.pending()
        if pend:
            add("approvals", "warn",
                f"{len(pend)} pending approval(s) — AI may be blocked",
                "Review: precept approval list")
        else:
            add("approvals", "ok", "No pending approvals")
    except Exception:
        pass

    # 6. Cognition stamp freshness
    stamp = target / ".precept" / "last_cognition.json"
    if stamp.exists():
        try:
            data = json.loads(stamp.read_text(encoding="utf-8"))
            ts = data.get("timestamp", "")
            when = datetime.fromisoformat(ts.replace("Z", ""))
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            age_min = int((now - when).total_seconds() / 60)
            if age_min < 60:
                add("cognition", "ok", f"Last analyze_intent {age_min} min ago — fresh")
            else:
                add("cognition", "warn", f"Last analyze_intent {age_min} min ago — stale",
                    "Ask Claude to re-run analyze_intent before committing.")
        except Exception:
            add("cognition", "warn", "Could not parse cognition stamp")
    else:
        add("cognition", "skip", "No analyze_intent run yet in this repo")

    # ----------------- render -----------------
    if json_output:
        print(json.dumps({"target": str(target), "results": results}, indent=2, ensure_ascii=False))
        return

    icon = {"ok": "[green]+[/green]", "warn": "[yellow]![/yellow]",
            "fail": "[red]x[/red]", "skip": "[dim]-[/dim]"}
    t = Table(title=f"Precept doctor — {target.name}", show_header=True)
    t.add_column("", width=2)
    t.add_column("Check", style="bold")
    t.add_column("Detail")
    t.add_column("Fix", style="dim")
    for r in results:
        t.add_row(icon.get(r["status"], "?"), r["check"], r["detail"], r["fix"])
    console.print(t)

    fail_count = sum(1 for r in results if r["status"] == "fail")
    warn_count = sum(1 for r in results if r["status"] == "warn")
    if fail_count:
        console.print(f"\n[red]{fail_count} blocker(s).[/red] Fix these before relying on Precept.")
        raise typer.Exit(1)
    if warn_count:
        console.print(f"\n[yellow]{warn_count} warning(s).[/yellow] Setup works but is not optimal.")
    else:
        console.print("\n[green]All checks passed.[/green]")


@app.command()
def audit(
    action: str = typer.Argument("show", help="show | clear | path"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    limit: int = typer.Option(30, "--limit", "-n", help="How many most-recent events to show"),
    tool_filter: str = typer.Option("", "--tool", help="Only show events for this tool (e.g. analyze_intent)"),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSONL instead of a table"),
):
    """
    Inspect which Precept MCP tools the AI has called in this repo.

    The audit log is a single capped JSONL file at .precept/audit.log (last
    ~500 events, oldest dropped automatically). No log rotation needed.

    \b
    precept audit                       # last 30 events as a table
    precept audit --limit 100           # last 100
    precept audit --tool analyze_intent # only this tool
    precept audit --json                # raw JSON lines for scripting
    precept audit clear                 # delete the log
    precept audit path                  # print the log file path
    """
    from precept import audit as _audit

    if action == "path":
        print(_audit._audit_path(repo_path))
        return

    if action == "clear":
        if _audit.clear(repo_path):
            console.print("[green]Audit log cleared.[/green]")
        else:
            console.print("[yellow]No audit log to clear.[/yellow]")
        return

    if action != "show":
        console.print(f"[red]Unknown action '{action}'.[/red] Use: show | clear | path")
        raise typer.Exit(1)

    events = _audit.read(repo_path, limit=max(limit, 1))
    if tool_filter:
        events = [e for e in events if e.get("tool") == tool_filter]

    if json_output:
        for e in events:
            print(json.dumps(e, ensure_ascii=False))
        return

    if not events:
        console.print("[yellow]No audit events yet.[/yellow]  [dim](The AI hasn't called any Precept tools in this repo, or the log was cleared.)[/dim]")
        return

    t = Table(title=f"Precept audit — last {len(events)} event(s)", show_header=True)
    t.add_column("When (UTC)", style="dim", width=20)
    t.add_column("Tool", style="cyan")
    t.add_column("Args")
    for e in events:
        args = e.get("args") or {}
        rendered = ", ".join(f"{k}={_short(v)}" for k, v in args.items())
        t.add_row(e.get("ts", ""), e.get("tool", ""), rendered or "[dim](none)[/dim]")
    console.print(t)
    console.print(f"\n[dim]Log file: {_audit._audit_path(repo_path)}  (capped at ~500 lines)[/dim]")


def _short(v: object, max_len: int = 60) -> str:
    s = str(v)
    return s if len(s) <= max_len else s[:max_len] + "…"


@app.command(name="commit-check")
def commit_check(
    repo_path: str = typer.Option(".", "--repo", "-r"),
    strict: bool = typer.Option(False, "--strict", help="Fail on any warning, not just blockers"),
    stale_minutes: int = typer.Option(60, "--stale-minutes", help="Cognition older than this is considered stale"),
):
    """
    Gate commits: ensure AI ran analyze_intent recently and the decision allows proceeding.

    \b
    precept commit-check              # warns only
    precept commit-check --strict     # exits 1 on any issue
    """
    from datetime import datetime, timedelta, timezone

    stamp_path = Path(repo_path) / ".precept" / "last_cognition.json"
    if not stamp_path.exists():
        msg = "No cognition stamp found. AI should call `analyze_intent` before coding."
        console.print(f"[yellow]⚠ {msg}[/yellow]")
        if strict:
            raise typer.Exit(1)
        return

    try:
        stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]Invalid cognition stamp:[/red] {e}")
        raise typer.Exit(1 if strict else 0)

    # check freshness
    ts = stamp.get("timestamp", "")
    try:
        when = datetime.fromisoformat(ts.replace("Z", ""))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        age = now - when
        if age > timedelta(minutes=stale_minutes):
            msg = f"Cognition stamp is stale ({int(age.total_seconds() / 60)} min old). Re-run analyze_intent."
            console.print(f"[yellow]⚠ {msg}[/yellow]")
            if strict:
                raise typer.Exit(1)
    except ValueError:
        pass

    decision = stamp.get("decision", "")
    risk = stamp.get("risk_level", "")
    request = stamp.get("request", "")

    if decision == "reject":
        console.print(f"[red]✗ Last cognition REJECTED:[/red] {request}")
        console.print("[red]Do not commit. Address the rejection reason and re-analyze.[/red]")
        raise typer.Exit(1)

    if decision == "ask":
        console.print(f"[yellow]⚠ Last cognition requires APPROVAL:[/yellow] {request}")
        console.print(f"   Risk: {risk}. Run [cyan]precept approval list[/cyan] and ensure it's approved.")
        if strict:
            raise typer.Exit(1)
        return

    console.print(f"[green]✓ Cognition OK[/green] — decision: {decision}, risk: {risk}")
    console.print(f"   Request: {request}")


@app.command()
def check(
    request: str = typer.Argument("", help="Change request to evaluate. If omitted, read from stdin."),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    strict: bool = typer.Option(False, "--strict", help="Also fail on an 'ask' decision, not just 'reject'."),
):
    """
    Evaluate a change request and fail (non-zero exit) if Precept would block it.

    Exit codes: proceed/warn → 0, ask → 1 (only with --strict), reject → 2.
    Designed for CI: pipe a PR title/body in and gate the merge.

    \b
    precept check "add Google SSO to /login"
    printf '%s' "$PR_TITLE" | precept check --strict
    """
    if not request.strip():
        request = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    if not request:
        console.print("[red]No request provided.[/red] Pass it as an argument or via stdin.")
        raise typer.Exit(2)

    engine, _, _ = _load_engine(repo_path)
    with console.status("[bold cyan]Reasoning…"):
        report = engine.analyze(request)

    decision = report.risk.decision.value
    level = report.risk.level.value
    color = {"proceed": "green", "warn": "yellow", "ask": "blue", "reject": "red"}[decision]
    console.print(Panel(
        f"[bold {color}]{decision.upper()}[/bold {color}] — Risk: [bold]{level.upper()}[/bold]\n{request}",
        title="[bold]Precept check[/bold]",
    ))
    for w in report.risk.warnings:
        console.print(f"  [yellow]![/yellow] {w}")

    if decision == "reject":
        console.print("[red]✗ Blocked — this change needs explicit human sign-off.[/red]")
        raise typer.Exit(2)
    if decision == "ask" and strict:
        console.print("[yellow]⚠ Needs human approval before it can proceed (strict mode).[/yellow]")
        raise typer.Exit(1)
    console.print("[green]✓ Allowed[/green]")


@app.command()
def sync(
    action: str = typer.Argument("now", help="now | watch | init | pull | push | status"),
    workspace_name: str = typer.Option("", "--workspace", "-w", help="Workspace name (auto-detect from cwd if linked)"),
    remote: str = typer.Option("", "--remote", help="Remote URL (for init)"),
    branch: str = typer.Option("main", "--branch"),
    message: str = typer.Option("precept: update knowledge", "--message", "-m"),
    interval: int = typer.Option(60, "--interval", help="(watch) seconds between sync cycles"),
    no_auto_resolve: bool = typer.Option(False, "--no-auto-resolve", help="Don't auto-merge JSON conflicts"),
):
    """
    Sync the central workspace via git.

    \b
    precept sync                # one-shot: pull → push (default action: now)
    precept sync watch          # daemon: pull → push every --interval seconds
    precept sync status         # show local vs remote state
    precept sync init --remote git@github.com:org/x-knowledge.git
    precept sync pull           # pull only
    precept sync push -m "..."  # push only

    `now` and `watch` are also triggered automatically by `precept memory decide`,
    `precept approval approve|reject`, and `precept init` — so most users never
    need to run them by hand. Disable with `PRECEPT_AUTO_SYNC=0`.
    """
    if action in ("now", "watch"):
        from precept import sync as _sync_mod

        ws_dir = _resolve_workspace_dir(".")
        if ws_dir is None and workspace_name:
            from precept.paths import workspace_dir
            ws_dir = workspace_dir(workspace_name)
        if ws_dir is None or not ws_dir.exists():
            console.print("[red]No workspace found.[/red] Run `precept init` in a knowledge or working repo first.")
            raise typer.Exit(1)

        def cycle() -> int:
            pr, ph = _sync_mod.full_sync(ws_dir, message=message)
            for label, r in (("pull", pr), ("push", ph)):
                if r.action == "skip":
                    console.print(f"[dim]{label}: skipped ({r.skipped_reason})[/dim]")
                elif r.ok:
                    console.print(f"[green]+[/green] {label}: {r.detail or 'ok'}")
                else:
                    console.print(f"[red]x[/red] {label}: {r.detail}")
            return 0 if (pr.ok and ph.ok) else 1

        if action == "now":
            raise typer.Exit(cycle())

        # watch
        import time
        console.print(f"[bold]precept sync watch[/bold] — every {interval}s. Ctrl+C to stop.")
        try:
            while True:
                cycle()
                time.sleep(max(interval, 5))
        except KeyboardInterrupt:
            console.print("\n[dim]stopped.[/dim]")
            return


    from precept.link.resolver import resolve_workspace
    from precept.sync.git_sync import GitSync

    if not workspace_name:
        res = resolve_workspace(".")
        if res:
            workspace_name = res.workspace_name
        else:
            console.print("[red]No workspace specified and current dir is not linked.[/red]")
            console.print("Pass [cyan]--workspace <name>[/cyan] or run [cyan]precept link <name>[/cyan].")
            raise typer.Exit(1)

    sync_obj = GitSync(workspace_name)

    if action == "init":
        sync_obj.init(remote_url=remote, branch=branch)
        st = sync_obj.status()
        console.print(f"[green]Initialized[/green] git sync for workspace [bold]{workspace_name}[/bold]")
        console.print(f"  Path: {st.path}")
        if st.has_remote:
            console.print(f"  Remote: {st.remote_url}")
            console.print("\nNext: [cyan]precept sync push[/cyan]")
        else:
            console.print("  Remote: [yellow](none — pass --remote to set one)[/yellow]")
        return

    if action == "status":
        st = sync_obj.status()
        if not sync_obj.is_git_repo():
            console.print(f"[yellow]Workspace '{workspace_name}' is not git-initialized.[/yellow]")
            console.print("Run: [cyan]precept sync init --remote <url>[/cyan]")
            return
        console.print(Panel(
            f"[bold]Workspace:[/bold] {st.workspace}\n"
            f"[bold]Path:[/bold] {st.path}\n"
            f"[bold]Branch:[/bold] {st.branch}\n"
            f"[bold]Remote:[/bold] {st.remote_url or '(none)'}\n"
            f"[bold]Ahead/Behind:[/bold] {st.ahead}/{st.behind}\n"
            f"[bold]Dirty:[/bold] {'yes' if st.dirty else 'no'}\n"
            f"[bold]Unmerged:[/bold] {', '.join(st.unmerged) if st.unmerged else 'none'}",
            title="[bold]Sync Status[/bold]",
        ))
        return

    if action == "pull":
        ok, msg = sync_obj.pull(auto_resolve=not no_auto_resolve)
        if ok:
            console.print(f"[green]✓[/green] {msg}")
        else:
            console.print(f"[red]✗[/red] {msg}")
            raise typer.Exit(1)
        return

    if action == "push":
        ok, msg = sync_obj.push(message=message)
        if ok:
            console.print(f"[green]✓[/green] {msg}")
        else:
            console.print(f"[red]✗[/red] {msg}")
            raise typer.Exit(1)
        return

    console.print(f"[red]Unknown action '{action}'[/red]. Use: init | pull | push | status")
    raise typer.Exit(1)


_QUICKSTART_ENV = """\
POSTGRES_USER=precept
POSTGRES_PASSWORD=precept
POSTGRES_DB=precept
POSTGRES_PORT=5432
WEB_PORT=8080
"""

# Postgres only — the dashboard runs locally via `precept web`, so quickstart
# needs no published container image.
_QUICKSTART_COMPOSE = """\
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: precept-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports: ["${POSTGRES_PORT}:5432"]
    volumes: [precept_pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
      interval: 5s

volumes:
  precept_pgdata:
"""


@app.command()
def quickstart(
    repo_path: str = typer.Option(".", "--repo", "-r", help="Where to scaffold .env + docker-compose.yml"),
    no_docker: bool = typer.Option(False, "--no-docker", help="Skip starting Postgres + dashboard"),
    no_mcp: bool = typer.Option(False, "--no-mcp", help="Skip registering the MCP server with Claude Code"),
):
    """
    Zero to a working Precept setup in one command.

    Scaffolds .env + docker-compose.yml, starts Postgres + the dashboard,
    registers the MCP server with Claude Code, and installs the /precept slash
    commands. Safe to re-run — existing files are left untouched.
    """
    import shutil
    import subprocess

    target = Path(repo_path).resolve()

    # 1. Scaffold config files (never overwrite — quickstart is re-runnable).
    for name, content in ((".env", _QUICKSTART_ENV), ("docker-compose.yml", _QUICKSTART_COMPOSE)):
        path = target / name
        if path.exists():
            console.print(f"  [dim]skip[/dim]  {name} (exists)")
        else:
            path.write_text(content, encoding="utf-8")
            console.print(f"  [green]wrote[/green] {name}")

    # 2. Bring up Postgres + dashboard.
    if no_docker:
        console.print("[dim]Skipping container startup (--no-docker).[/dim]")
    elif shutil.which("docker") is None:
        console.print("[yellow]docker not found — skipping container startup.[/yellow] Install Docker, then re-run.")
    else:
        with console.status("[cyan]Starting Postgres + dashboard…"):
            rc = subprocess.run(["docker", "compose", "up", "-d"], cwd=str(target)).returncode
        if rc == 0:
            console.print("  [green]up[/green]    Postgres + dashboard")
        else:
            console.print("  [yellow]docker compose exited non-zero — check the output above.[/yellow]")

    # 3. Register the MCP server with Claude Code.
    if no_mcp:
        console.print("[dim]Skipping MCP registration (--no-mcp).[/dim]")
    else:
        # On Windows, `claude` is installed as `claude.cmd` (npm shim). Python's
        # subprocess.run doesn't resolve PATHEXT — pass the full path from
        # shutil.which so the .cmd extension is found.
        claude_exe = shutil.which("claude")
        if claude_exe is None:
            console.print("[yellow]Claude Code CLI not found — skipping MCP registration.[/yellow]")
            console.print("  Install it, then run: [cyan]claude mcp add precept -- precept mcp[/cyan]")
        else:
            rc = subprocess.run(
                [claude_exe, "mcp", "add", "precept", "--", "precept", "mcp"],
                cwd=str(target),
            ).returncode
            if rc == 0:
                console.print("  [green]ok[/green]    registered MCP server 'precept'")

    # 4. Install the /precept slash commands.
    try:
        install_claude_commands(user=True, force=False)
    except SystemExit:
        pass

    # 5. Next steps.
    console.print(Panel(
        "Open Claude Code in any repo and try:\n"
        "  [cyan]/precept add Google SSO to /login[/cyan]\n\n"
        "Open the dashboard:\n"
        "  [cyan]precept web[/cyan]  →  http://localhost:8080",
        title="[bold green]Precept is ready[/bold green]",
    ))


# alias: `precept up`
app.command(name="up")(quickstart)


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", "--host", help="Bind address"),
    port: int = typer.Option(8080, "--port", "-p", help="Port for the dashboard"),
):
    """
    Run the Precept dashboard locally.

    Reads the same POSTGRES_* env / precept.config as the MCP server, so it
    shows the memory, approvals, syntheses, and audit log for your team.
    """
    import uvicorn

    console.print(f"[bold green]Precept dashboard[/bold green] → http://localhost:{port}  [dim](Ctrl-C to stop)[/dim]")
    uvicorn.run("precept.web.app:app", host=host, port=port)


@app.command()
def mcp_server(
    repo_path: str = typer.Option(".", "--repo", "-r", help="Default repo path for MCP tools"),
    sse: bool = typer.Option(False, "--sse", help="Run as SSE server instead of stdio"),
    port: int = typer.Option(8765, "--port", "-p"),
):
    """Start the Precept MCP server (stdio by default, --sse for HTTP)."""
    from precept.mcp.server import mcp
    console.print(f"[bold green]Starting Precept MCP server[/bold green] ({'SSE' if sse else 'stdio'})")
    if sse:
        mcp.run(transport="sse", host="127.0.0.1", port=port)
    else:
        mcp.run(transport="stdio")


# entry point alias for the mcp subcommand
app.command(name="mcp")(mcp_server)


_MCP_JSON = """{
  "mcpServers": {
    "precept": { "command": "precept", "args": ["mcp"] }
  }
}"""

# VS Code's native MCP support uses a "servers" key instead of "mcpServers".
_MCP_JSON_VSCODE = """{
  "servers": {
    "precept": { "command": "precept", "args": ["mcp"] }
  }
}"""

_MCP_CLIENTS = {
    "claude": ("Claude Code", "Run:\n    claude mcp add precept -- precept mcp"),
    "cursor": ("Cursor", "Add to ~/.cursor/mcp.json (or .cursor/mcp.json in a project):\n" + _MCP_JSON),
    "windsurf": ("Windsurf", "Add to ~/.codeium/windsurf/mcp_config.json:\n" + _MCP_JSON),
    "cline": ("Cline (VS Code)", "Add to Cline's cline_mcp_settings.json:\n" + _MCP_JSON),
    "vscode": ("VS Code / Copilot agent", "Add to .vscode/mcp.json:\n" + _MCP_JSON_VSCODE),
    "json": ("Generic MCP client", "Most clients use this shape:\n" + _MCP_JSON),
}


@app.command(name="mcp-config")
def mcp_config(
    client: str = typer.Argument("json", help="claude | cursor | vscode | windsurf | cline | json"),
):
    """
    Print the MCP setup for your AI client.

    precept is a standard stdio MCP server, so any MCP-capable agent (Claude
    Code, Cursor, VS Code/Copilot, Windsurf, Cline, …) can use it — the command
    is always `precept mcp`.
    """
    key = client.lower()
    if key == "all":
        for label, body in _MCP_CLIENTS.values():
            console.print(f"\n[bold cyan]{label}[/bold cyan]")
            print(body)
        return
    entry = _MCP_CLIENTS.get(key)
    if not entry:
        console.print(f"[red]Unknown client '{client}'.[/red] Options: {', '.join(_MCP_CLIENTS)} (or 'all').")
        raise typer.Exit(1)
    label, body = entry
    console.print(f"[bold cyan]{label}[/bold cyan]")
    print(body)


def run() -> None:
    """Console-script entry point.

    Shortcut: `precept "<request>"` behaves like `precept analyze "<request>"`
    when the first argument isn't a known subcommand — so you can just type a
    request without remembering the command name.
    """
    argv = sys.argv[1:]
    if argv and not argv[0].startswith("-"):
        known: set[str] = set()
        for cmd in app.registered_commands:
            name = cmd.name or (cmd.callback.__name__.replace("_", "-") if cmd.callback else None)
            if name:
                known.add(name)
        if argv[0] not in known:
            sys.argv.insert(1, "analyze")
    app()


if __name__ == "__main__":
    run()
