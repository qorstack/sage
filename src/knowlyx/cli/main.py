"""Knowlyx CLI — cognitive enforcement for AI development."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="knowlyx",
    help="Cognitive enforcement layer for AI software development.",
    no_args_is_help=True,
)
console = Console()


def _load_engine(repo_path: str):
    from knowlyx.graph.cognitive_graph import CognitiveGraph
    from knowlyx.reasoning.engine import ReasoningEngine
    from knowlyx.scanner.repo_scanner import RepoScanner

    _print_workspace_hint(repo_path)
    scanner = RepoScanner(repo_path)
    with console.status("[bold cyan]Scanning repository…"):
        scan = scanner.scan()
    graph = CognitiveGraph()
    graph.build(scan)
    engine = ReasoningEngine(scan, graph)
    return engine, scan, graph


def _print_workspace_hint(repo_path: str) -> None:
    """Print a one-line setup hint if the shared knowledge isn't on this machine."""
    try:
        from knowlyx.link.resolver import workspace_setup_hint
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
    from knowlyx.scanner.repo_scanner import RepoScanner

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
        title="[bold green]Knowlyx Scan[/bold green]",
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
    from knowlyx.scanner.repo_scanner import RepoScanner
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
    from knowlyx.reasoning.impact_analyzer import ImpactAnalyzer
    from knowlyx.reasoning.intent_analyzer import IntentAnalyzer

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
    from knowlyx.scanner.repo_scanner import RepoScanner
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
    query: str = typer.Argument("", help="Search query or entry ID"),
    domain: str = typer.Option("", "--domain", "-d"),
    title: str = typer.Option("", "--title"),
    body: str = typer.Option("", "--body"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
):
    """
    Manage Knowlyx memory.

    \b
    knowlyx memory list                        # list all entries
    knowlyx memory recall "payment idempotency"
    knowlyx memory decide payment "Use Redis queue" --body "All async jobs via BullMQ"
    knowlyx memory forget <entry-id>
    """
    from knowlyx.memory.schema import MemoryEntry, MemoryKind
    from knowlyx.memory.store import create_store
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
            t.add_row(e.id, e.kind.value, e.domain, e.title, "[green]✓[/green]" if e.approved else "[yellow]pending[/yellow]")
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
        if not query or not body:
            console.print("[red]Usage: knowlyx memory decide <domain> <title> --body <decision>[/red]")
            raise typer.Exit(1)
        entry = MemoryEntry(id="", kind=MemoryKind.TEAM_DECISION, domain=query, title=title or body[:60], body=body, approved=True, approved_by="team", repo_path=repo_path)
        saved = store.save(entry)
        console.print(f"[green]Decision saved and approved[/green] — ID: {saved.id}")

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
    from knowlyx.packs.builtin import get_pack
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
    knowlyx workspace init                        # create knowlyx.toml in cwd (legacy)
    knowlyx workspace create my-product           # create central workspace at ~/.knowlyx/workspaces/
    knowlyx workspace list                        # list all central workspaces
    knowlyx workspace scan                        # scan all repos
    knowlyx workspace impact api -c "rename users.email"
    knowlyx workspace graph                       # print mermaid diagram
    knowlyx workspace graph react_flow --json     # React Flow JSON
    """
    from knowlyx.workspace.config_loader import init, load
    from knowlyx.workspace.multi_scanner import CrossRepoImpactAnalyzer, WorkspaceScanner

    if action == "init":
        cfg = init(workspace_path)
        console.print(f"[green]Created[/green] knowlyx.toml for workspace '{cfg.name}'")
        console.print("Edit knowlyx.toml to add [[repos]] and [[dependencies]] sections.")
        return

    if action == "create":
        if not target:
            console.print("[red]Provide workspace name:[/red] knowlyx workspace create <name>")
            raise typer.Exit(1)
        from knowlyx.paths import ensure_workspace_dir, workspace_toml_path
        from knowlyx.workspace.config_loader import _serialize
        from knowlyx.workspace.schema import WorkspaceConfig
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
        console.print(f"\nNext: in each repo, run [cyan]knowlyx link {target}[/cyan]")
        return

    if action == "list":
        from knowlyx.paths import knowlyx_home, list_workspaces
        names = list_workspaces()
        if json_output:
            print(json.dumps({"home": str(knowlyx_home()), "workspaces": names}, indent=2))
            return
        console.print(f"[bold]Central workspaces[/bold] at {knowlyx_home()}")
        if not names:
            console.print("  [dim](none — run `knowlyx workspace create <name>` to add one)[/dim]")
            return
        for n in names:
            console.print(f"  • [cyan]{n}[/cyan]")
        return

    config = load(workspace_path)
    if not config.repos and action != "init":
        console.print("[yellow]No repos in knowlyx.toml. Add [[repos]] entries first.[/yellow]")
        raise typer.Exit(1)

    if action == "cache":
        from knowlyx.cache.scan_cache import ScanCache
        from knowlyx.link.resolver import resolve_workspace
        res = resolve_workspace(workspace_path)
        ws_name = res.workspace_name if res else config.name
        cache = ScanCache(ws_name)
        names = cache.list_cached()
        if json_output:
            print(json.dumps([cache.metadata(n) for n in names], indent=2))
            return
        if not names:
            console.print(f"[yellow]No cached scans for workspace '{ws_name}'.[/yellow]")
            console.print("Run [cyan]knowlyx workspace scan --persist[/cyan] on a machine with the repos cloned.")
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
            console.print("[red]Specify repo name: knowlyx workspace impact <repo-name> --change '...'[/red]")
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
        from knowlyx.graph.exporter import GraphExporter
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
    knowlyx approval list              # list pending approvals
    knowlyx approval show <id>         # show details
    knowlyx approval approve <id>
    knowlyx approval reject <id> --reason "too risky right now"
    """
    from knowlyx.approval.queue import get_queue

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

    elif action == "reject":
        if not request_id:
            console.print("[red]Provide a request ID.[/red]")
            raise typer.Exit(1)
        req = queue.reject(request_id, reason)
        if not req:
            console.print(f"[red]Not found:[/red] {request_id}")
            raise typer.Exit(1)
        console.print(f"[red]Rejected[/red] — {req.title}" + (f" ({reason})" if reason else ""))
    else:
        console.print(f"[red]Unknown action '{action}'[/red]. Use: list | show | approve | reject")


@app.command()
def graph(
    format: str = typer.Argument("mermaid", help="mermaid | dot | react_flow"),
    repo_path: str = typer.Option(".", "--repo", "-r"),
):
    """Export the cognitive graph for a single repo."""
    from knowlyx.graph.cognitive_graph import CognitiveGraph
    from knowlyx.graph.exporter import GraphExporter
    from knowlyx.scanner.repo_scanner import RepoScanner

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
    knowlyx link my-product --role backend --domains billing,auth --critical \\
                            --remote git@github.com:org/my-product-knowledge.git
    """
    from knowlyx.link.config import LinkConfig, save_link
    from knowlyx.paths import workspace_dir, workspace_toml_path

    ws_exists_locally = workspace_toml_path(workspace_name).exists()
    if not ws_exists_locally and not remote:
        console.print(f"[red]Workspace '{workspace_name}' does not exist locally and no --remote provided.[/red]")
        console.print(f"Either: [cyan]knowlyx workspace create {workspace_name}[/cyan]")
        console.print(f"Or:     [cyan]knowlyx link {workspace_name} --remote <git-url>[/cyan]  (clone shared knowledge)")
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
    """Remove this repo's link to a central workspace (deletes .knowlyx/config.toml)."""
    from knowlyx.paths import repo_link_config_path

    path = repo_link_config_path(repo_path)
    if not path.exists():
        console.print("[yellow]No link config found.[/yellow]")
        raise typer.Exit(0)
    path.unlink()
    console.print(f"[green]Unlinked[/green] {path}")


@app.command()
def migrate(
    repo_path: str = typer.Option(".", "--repo", "-r"),
    workspace_name: str = typer.Option("", "--workspace", "-w", help="Target workspace (must exist)"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """
    Migrate legacy per-repo .knowlyx/{memory,approvals}.json into a central workspace.

    \b
    1. knowlyx workspace create my-product
    2. knowlyx link my-product --repo /path/to/api
    3. knowlyx migrate --repo /path/to/api
    """
    import json as _json

    from knowlyx.link.config import load_link
    from knowlyx.paths import workspace_approvals_path, workspace_memory_path

    legacy_dir = Path(repo_path) / ".knowlyx"
    legacy_memory = legacy_dir / "memory.json"
    legacy_approvals = legacy_dir / "approvals.json"

    if not legacy_memory.exists() and not legacy_approvals.exists():
        console.print("[yellow]Nothing to migrate.[/yellow] No legacy .knowlyx/memory.json or approvals.json found.")
        raise typer.Exit(0)

    if not workspace_name:
        link = load_link(repo_path)
        if not link:
            console.print("[red]No workspace specified and no link config found.[/red]")
            console.print("Either pass --workspace <name> or run `knowlyx link <name>` first.")
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
    workspace_mode: bool = typer.Option(False, "--workspace", help="Init workspace folder (auto-detect repos as siblings)"),
    name: str = typer.Option("", "--name", help="Workspace name (defaults to folder name)"),
    link_to: str = typer.Option("", "--link", help="Link this repo to an existing central workspace"),
    remote: str = typer.Option("", "--remote", help="Git URL of shared knowledge repo (recorded so teammates know where to clone)"),
):
    """
    Scaffold Knowlyx for a project.

    \b
    knowlyx init                                          # scan repo + suggest setup
    knowlyx init --workspace                              # legacy: create knowlyx.toml in cwd
    knowlyx init --link my-product                        # link to existing local workspace
    knowlyx init --link my-product --remote git@...:org/knowledge.git
                                                          # link + record where teammates clone
    """
    from knowlyx.scanner.repo_scanner import RepoScanner

    target = Path(repo_path).resolve()

    if link_to:
        from knowlyx.link.config import LinkConfig, save_link
        from knowlyx.paths import workspace_dir, workspace_toml_path
        ws_exists_locally = workspace_toml_path(link_to).exists()
        if not ws_exists_locally and not remote:
            console.print(f"[red]Workspace '{link_to}' not found locally and no --remote provided.[/red]")
            console.print(f"Either: [cyan]knowlyx workspace create {link_to}[/cyan]")
            console.print(f"Or:     [cyan]knowlyx init --link {link_to} --remote <git-url>[/cyan]")
            raise typer.Exit(1)
        # auto-detect role + domains
        with console.status("[bold cyan]Auto-detecting role + domains…"):
            scan = RepoScanner(target).scan()
        role = _infer_role(scan.framework, scan.language)
        save_link(LinkConfig(
            workspace=link_to,
            repo_name=target.name,
            role=role,
            domains=scan.domains[:6],
            knowledge_remote=remote,
        ), target)
        console.print(f"[green]Linked[/green] {target.name} → {link_to}")
        console.print(f"  Role: {role}, Domains: {', '.join(scan.domains[:6]) or '(none)'}")
        if remote:
            console.print(f"  Knowledge remote: {remote}")
        console.print("  Commit [cyan].knowlyx/config.toml[/cyan] to git so teammates get linked automatically.")
        if not ws_exists_locally and remote:
            console.print(
                f"\n[yellow]⚠ Shared knowledge not on this machine yet.[/yellow]\n"
                f"  Run:  [cyan]git clone {remote} {workspace_dir(link_to)}[/cyan]"
            )
        return

    if workspace_mode:
        from knowlyx.workspace.config_loader import init as ws_init
        cfg = ws_init(target, name=name)
        console.print(f"[green]Created[/green] knowlyx.toml for workspace '{cfg.name}'")
        console.print("Add [[repos]] and [[dependencies]] sections to knowlyx.toml.")
        return

    # default: scan + suggest
    with console.status("[bold cyan]Scanning repo…"):
        scan = RepoScanner(target).scan()
    role = _infer_role(scan.framework, scan.language)
    console.print(Panel(
        f"[bold]Folder:[/bold] {target.name}\n"
        f"[bold]Stack:[/bold] {scan.language} / {scan.framework}\n"
        f"[bold]Architecture:[/bold] {scan.architecture.value}\n"
        f"[bold]Suggested role:[/bold] [cyan]{role}[/cyan]\n"
        f"[bold]Detected domains:[/bold] {', '.join(scan.domains) or '(none)'}",
        title="[bold green]Knowlyx Init[/bold green]",
    ))
    console.print("\n[bold]Suggested next steps:[/bold]\n")
    console.print("  1. Create central workspace:")
    console.print(f"     [cyan]knowlyx workspace create {name or target.name}[/cyan]\n")
    console.print("  2. Link this repo:")
    suggested_link = f"knowlyx init --link {name or target.name}"
    console.print(f"     [cyan]{suggested_link}[/cyan]\n")
    console.print("  3. Add MCP server to .claude/settings.json:")
    console.print('     [dim]{"mcpServers": {"knowlyx": {"command": "uvx", "args": ["knowlyx", "mcp", "--repo", "."]}}}[/dim]')


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


@app.command(name="commit-check")
def commit_check(
    repo_path: str = typer.Option(".", "--repo", "-r"),
    strict: bool = typer.Option(False, "--strict", help="Fail on any warning, not just blockers"),
    stale_minutes: int = typer.Option(60, "--stale-minutes", help="Cognition older than this is considered stale"),
):
    """
    Gate commits: ensure AI ran analyze_intent recently and the decision allows proceeding.

    \b
    knowlyx commit-check              # warns only
    knowlyx commit-check --strict     # exits 1 on any issue
    """
    from datetime import datetime, timedelta, timezone

    stamp_path = Path(repo_path) / ".knowlyx" / "last_cognition.json"
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
        console.print(f"   Risk: {risk}. Run [cyan]knowlyx approval list[/cyan] and ensure it's approved.")
        if strict:
            raise typer.Exit(1)
        return

    console.print(f"[green]✓ Cognition OK[/green] — decision: {decision}, risk: {risk}")
    console.print(f"   Request: {request}")


@app.command()
def sync(
    action: str = typer.Argument(..., help="init | pull | push | status"),
    workspace_name: str = typer.Option("", "--workspace", "-w", help="Workspace name (auto-detect from cwd if linked)"),
    remote: str = typer.Option("", "--remote", help="Remote URL (for init)"),
    branch: str = typer.Option("main", "--branch"),
    message: str = typer.Option("knowlyx: update knowledge", "--message", "-m"),
    no_auto_resolve: bool = typer.Option(False, "--no-auto-resolve", help="Don't auto-merge JSON conflicts"),
):
    """
    Sync the central workspace via git (GitHub/GitLab/self-hosted).

    \b
    knowlyx sync init --remote git@github.com:org/x-product-knowledge.git
    knowlyx sync pull
    knowlyx sync push -m "decision: use stripe billing"
    knowlyx sync status
    """
    from knowlyx.link.resolver import resolve_workspace
    from knowlyx.sync.git_sync import GitSync

    if not workspace_name:
        res = resolve_workspace(".")
        if res:
            workspace_name = res.workspace_name
        else:
            console.print("[red]No workspace specified and current dir is not linked.[/red]")
            console.print("Pass [cyan]--workspace <name>[/cyan] or run [cyan]knowlyx link <name>[/cyan].")
            raise typer.Exit(1)

    sync_obj = GitSync(workspace_name)

    if action == "init":
        sync_obj.init(remote_url=remote, branch=branch)
        st = sync_obj.status()
        console.print(f"[green]Initialized[/green] git sync for workspace [bold]{workspace_name}[/bold]")
        console.print(f"  Path: {st.path}")
        if st.has_remote:
            console.print(f"  Remote: {st.remote_url}")
            console.print("\nNext: [cyan]knowlyx sync push[/cyan]")
        else:
            console.print("  Remote: [yellow](none — pass --remote to set one)[/yellow]")
        return

    if action == "status":
        st = sync_obj.status()
        if not sync_obj.is_git_repo():
            console.print(f"[yellow]Workspace '{workspace_name}' is not git-initialized.[/yellow]")
            console.print("Run: [cyan]knowlyx sync init --remote <url>[/cyan]")
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


@app.command()
def mcp_server(
    repo_path: str = typer.Option(".", "--repo", "-r", help="Default repo path for MCP tools"),
    sse: bool = typer.Option(False, "--sse", help="Run as SSE server instead of stdio"),
    port: int = typer.Option(8765, "--port", "-p"),
):
    """Start the Knowlyx MCP server (stdio by default, --sse for HTTP)."""
    from knowlyx.mcp.server import mcp
    console.print(f"[bold green]Starting Knowlyx MCP server[/bold green] ({'SSE' if sse else 'stdio'})")
    if sse:
        mcp.run(transport="sse", host="127.0.0.1", port=port)
    else:
        mcp.run(transport="stdio")


# entry point alias for the mcp subcommand
app.command(name="mcp")(mcp_server)

if __name__ == "__main__":
    app()
