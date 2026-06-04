"""
precept dashboard — read-only web UI for monitoring memory entries,
syntheses, audit log, and supersession/merge activity.

Run: uvicorn precept.web.app:app --host 0.0.0.0 --port 9080

Uses the same POSTGRES_* / PRECEPT_DB_SCHEMA env vars as the store, so a single
.env file drives both backend and dashboard.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from precept.memory.postgres_store import PostgresMemoryStore
from precept.memory.schema import MemoryEntry, MemoryKind

KINDS = [k.value for k in MemoryKind]


def _store() -> PostgresMemoryStore:
    """Lazy single store — reuses the same merge/audit/embedding logic as MCP."""
    global _STORE  # noqa: PLW0603
    try:
        return _STORE
    except NameError:
        _STORE = PostgresMemoryStore()
        return _STORE

_PKG = resources.files("precept.web")
TEMPLATES = Jinja2Templates(directory=str(Path(str(_PKG / "templates"))))

app = FastAPI(title="precept dashboard")
app.mount("/static", StaticFiles(directory=str(Path(str(_PKG / "static")))), name="static")


def _pool():
    """Reuse the store's connection pool for read queries."""
    return _store()._pool


def _fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    with _pool().connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def _fetch_one(sql: str, params: tuple = ()) -> dict | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


_DECISION_LINE = {
    "proceed": "Safe to proceed — no blocking concerns found.",
    "warn": "Proceed with care — review the notes below before you write code.",
    "ask": "Pause — a human should confirm this before it ships.",
    "reject": "Stop — this needs explicit human sign-off before any code is written.",
}


def _playground_markdown(q: str, report, pack) -> str:
    """Render the cognition report as the same kind of markdown reply an agent
    posts back through MCP — so the playground reads like the real thing."""
    d = report.risk.decision.value
    lines: list[str] = []
    lines.append(f"**Decision: {d.upper()}**  ·  Risk: **{report.risk.level.value.upper()}**")
    lines.append("")
    lines.append(f"> {_DECISION_LINE.get(d, '')}")
    lines.append("")
    lines.append(f"**Domain:** `{report.intent.detected_domain}`  **Action:** `{report.intent.detected_action}`")

    lines.append("\n**Reuse before creating new code**")
    if report.reusable_assets_to_use:
        for a in report.reusable_assets_to_use[:6]:
            lines.append(f"- `{a.name}` ({a.asset_type})")
    else:
        lines.append("- _Connect your repo and Precept names the exact assets to reuse here (e.g. `PaymentClient`) instead of letting the agent invent a new one._")

    rules = (pack.business_rules if pack else []) or []
    if rules:
        lines.append("\n**Team rules / domain policy that applies**")
        for r in rules[:5]:
            lines.append(f"- {r}")

    if report.risk.warnings:
        lines.append("\n**Why Precept paused**")
        for w in report.risk.warnings:
            lines.append(f"- {w}")

    if report.impact.cascade_risks:
        lines.append("\n**Blast radius**")
        for r in report.impact.cascade_risks:
            lines.append(f"- {r}")

    if pack and pack.forbidden_shortcuts:
        lines.append("\n**Do not**")
        for r in pack.forbidden_shortcuts[:4]:
            lines.append(f"- {r}")

    if report.suggested_plan:
        lines.append("\n**Suggested workflow**")
        for step in report.suggested_plan:
            # plan steps already start with "1." etc; normalize to a list
            lines.append(f"- {step.lstrip('0123456789. ')}")

    return "\n".join(lines)


@app.get("/playground", response_class=HTMLResponse)
def playground(request: Request, q: str = Query("")):
    """Public 'try it live' page — runs the real rule-based engine with no
    repo, no DB, and no LLM. Great for demos and the landing experience."""
    report_md = ""
    decision = ""
    if q.strip():
        from precept.graph.cognitive_graph import CognitiveGraph
        from precept.models.schema import ScanResult
        from precept.packs.builtin import get_pack
        from precept.reasoning.engine import ReasoningEngine

        scan = ScanResult(repo_path=".")
        graph = CognitiveGraph()
        graph.build(scan)
        report = ReasoningEngine(scan, graph).analyze(q)
        pack = get_pack(report.intent.detected_domain)
        report_md = _playground_markdown(q, report, pack)
        decision = report.risk.decision.value
    return TEMPLATES.TemplateResponse(
        request,
        "playground.html",
        {"q": q, "report_md": report_md, "decision": decision, "active": "playground"},
    )


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    stats = _fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM memory_entries WHERE superseded_by IS NULL) AS active_entries,
            (SELECT COUNT(*) FROM memory_entries WHERE superseded_by IS NOT NULL) AS superseded_entries,
            (SELECT COUNT(*) FROM memory_entries WHERE approved) AS approved_entries,
            (SELECT COUNT(*) FROM memory_entries WHERE source = 'ai' AND NOT approved AND superseded_by IS NULL) AS pending_ai,
            (SELECT COUNT(*) FROM memory_entries WHERE scope = 'global' AND superseded_by IS NULL) AS global_entries,
            (SELECT COUNT(*) FROM memory_syntheses) AS syntheses,
            (SELECT COUNT(*) FROM memory_syntheses WHERE stale) AS stale_syntheses,
            (SELECT COUNT(*) FROM memory_audit_log WHERE at > now() - interval '24 hours') AS audit_24h,
            (SELECT COUNT(*) FROM memory_audit_log WHERE action = 'merge') AS merges
        """,
    ) or {}
    workspaces = _list_workspaces()

    by_domain = _fetch_all(
        """
        SELECT domain, COUNT(*) AS n
        FROM memory_entries
        WHERE superseded_by IS NULL
        GROUP BY domain
        ORDER BY n DESC
        LIMIT 10
        """,
    )

    by_kind = _fetch_all(
        """
        SELECT kind::text AS kind, COUNT(*) AS n
        FROM memory_entries
        WHERE superseded_by IS NULL
        GROUP BY kind
        ORDER BY n DESC
        """,
    )

    recent_activity = _fetch_all(
        """
        SELECT a.at, a.action, a.actor, a.entry_id, e.title, e.domain
        FROM memory_audit_log a
        LEFT JOIN memory_entries e ON e.id = a.entry_id
        ORDER BY a.at DESC
        LIMIT 15
        """,
    )

    return TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "by_domain": by_domain,
            "by_kind": by_kind,
            "workspaces": workspaces,
            "recent_activity": recent_activity,
            "active": "dashboard",
        },
    )


def _render_entries(
    request: Request,
    *,
    q: str = "",
    domain: str = "",
    workspace: str = "",
    scope: str = "",
    source: str = "",
    status: str = "",
    show_superseded: bool = False,
    show_add: bool = False,
    form_title: str = "",
    form_body: str = "",
    form_approve: bool = False,
    form_scope: str = "global",
    form_workspace: str = "",
    error: str = "",
):
    where = []
    params: list = []
    if not show_superseded:
        where.append("superseded_by IS NULL")
    if domain:
        where.append("domain = %s")
        params.append(domain)
    if workspace == "__global__":
        where.append("scope = 'global'")
    elif workspace:
        where.append("scope = 'workspace' AND workspace = %s")
        params.append(workspace)
    if scope in ("global", "workspace"):
        where.append("scope = %s::memory_scope")
        params.append(scope)
    if source in ("human", "ai"):
        where.append("source = %s::memory_source")
        params.append(source)
    if status == "pending":
        where.append("NOT approved")
    elif status == "approved":
        where.append("approved")
    if q:
        where.append("search_tsv @@ plainto_tsquery('simple', %s)")
        params.append(q)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    rows = _fetch_all(
        f"""
        SELECT id, kind::text AS kind, domain, title,
               approved, updated_at, superseded_by,
               scope::text AS scope, source::text AS source,
               workspace, repo_name,
               COALESCE((metadata->>'merge_count')::int, 0) AS merge_count
        FROM memory_entries
        {where_sql}
        ORDER BY updated_at DESC
        LIMIT 200
        """,
        tuple(params),
    )

    return TEMPLATES.TemplateResponse(
        request,
        "entries.html",
        {
            "rows": rows,
            "domains": _list_domains(),
            "workspaces": _list_workspaces(),
            "filter_domain": domain,
            "filter_workspace": workspace,
            "filter_scope": scope,
            "filter_source": source,
            "filter_status": status,
            "filter_q": q,
            "show_superseded": show_superseded,
            "show_add": show_add or bool(error),
            "form_title": form_title,
            "form_body": form_body,
            "form_approve": form_approve,
            "form_scope": form_scope,
            "form_workspace": form_workspace,
            "error": error,
            "active": "entries",
        },
    )


@app.get("/entries", response_class=HTMLResponse)
def entries(
    request: Request,
    domain: str = Query("", alias="domain"),
    workspace: str = Query(""),
    scope: str = Query(""),
    source: str = Query(""),
    status: str = Query(""),
    q: str = Query("", alias="q"),
    show_superseded: bool = Query(False),
    add: bool = Query(False),
):
    return _render_entries(
        request,
        q=q,
        domain=domain,
        workspace=workspace,
        scope=scope,
        source=source,
        status=status,
        show_superseded=show_superseded,
        show_add=add,
    )


@app.get("/entries/{entry_id}", response_class=HTMLResponse)
def entry_detail(request: Request, entry_id: str):
    entry = _fetch_one(
        """
        SELECT id, kind::text AS kind, domain, title, body, tags,
               approved, approved_by, repo_path, metadata,
               scope::text AS scope, source::text AS source,
               workspace, repo_name,
               created_at, updated_at, superseded_by, superseded_at
        FROM memory_entries
        WHERE id = %s
        """,
        (entry_id,),
    )
    audit = _fetch_all(
        "SELECT at, action, actor, diff FROM memory_audit_log WHERE entry_id = %s ORDER BY at DESC",
        (entry_id,),
    )
    return TEMPLATES.TemplateResponse(
        request,
        "entry_detail.html",
        {"entry": entry, "audit": audit, "active": "entries"},
    )


@app.get("/syntheses", response_class=HTMLResponse)
def syntheses(request: Request):
    rows = _fetch_all(
        """
        SELECT s.domain, s.summary, s.key_themes, s.open_questions,
               s.synthesized_at, s.synthesized_by, s.entry_count_at_synthesis, s.stale,
               (SELECT COUNT(*) FROM memory_entries WHERE domain = s.domain AND superseded_by IS NULL) AS current_entries
        FROM memory_syntheses s
        ORDER BY s.stale DESC, s.synthesized_at DESC
        """,
    )
    return TEMPLATES.TemplateResponse(
        request,
        "syntheses.html",
        {"rows": rows, "active": "syntheses"},
    )


@app.get("/audit", response_class=HTMLResponse)
def audit(
    request: Request,
    action: str = Query("", alias="action"),
    limit: int = Query(100, ge=1, le=500),
):
    where = []
    params: list = []
    if action:
        where.append("a.action = %s")
        params.append(action)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    params.append(limit)

    rows = _fetch_all(
        f"""
        SELECT a.id, a.at, a.action, a.actor, a.entry_id, a.diff,
               e.title, e.domain
        FROM memory_audit_log a
        LEFT JOIN memory_entries e ON e.id = a.entry_id
        {where_sql}
        ORDER BY a.at DESC
        LIMIT %s
        """,
        tuple(params),
    )
    actions = ["insert", "update", "delete", "supersede", "approve", "merge"]
    return TEMPLATES.TemplateResponse(
        request,
        "audit.html",
        {
            "request": request,
            "rows": rows,
            "actions": actions,
            "filter_action": action,
            "limit": limit,
            "active": "audit",
        },
    )


# ---------------------------------------------------------------------------
# Team knowledge management — create / edit / approve / delete
# ---------------------------------------------------------------------------


def _author_from(request: Request, fallback: str = "") -> str:
    """Identity from sticky cookie set by /me. Fallback to form field or 'web'."""
    return request.cookies.get("precept_author") or fallback or "web"


def _parse_tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


def _list_domains() -> list[str]:
    return [r["domain"] for r in _fetch_all(
        "SELECT DISTINCT domain FROM memory_entries ORDER BY domain"
    )]


def _list_workspaces() -> list[dict]:
    """Workspaces that have at least one entry, with counts."""
    return _fetch_all(
        """
        SELECT workspace,
               COUNT(*) FILTER (WHERE approved)     AS approved,
               COUNT(*) FILTER (WHERE NOT approved) AS pending
        FROM memory_entries
        WHERE scope = 'workspace' AND workspace <> '' AND superseded_by IS NULL
        GROUP BY workspace
        ORDER BY workspace
        """
    )


_DEFAULT_DOMAIN = "general"
_DEFAULT_KIND = "team_decision"


def _validate_fields(kind: str, domain: str, title: str, body: str) -> str | None:
    if not title.strip():
        return "Title is required."
    if kind and kind not in KINDS:
        return f"Invalid type '{kind}'."
    if not body.strip():
        return "Body is empty. Write something in the editor below."
    return None


@app.get("/knowledge")
def knowledge_redirect(domain: str = Query("")):
    target = "/entries?add=true"
    if domain:
        target += f"&domain={domain}"
    return RedirectResponse(url=target, status_code=307)


@app.post("/knowledge/create", response_class=HTMLResponse)
def knowledge_create(
    request: Request,
    title: str = Form(""),
    body: str = Form(""),
    approve: bool = Form(False),
    scope: str = Form("global"),
    workspace: str = Form(""),
):
    from precept.memory.schema import MemoryScope, MemorySource

    kind = _DEFAULT_KIND
    domain = _DEFAULT_DOMAIN
    err = _validate_fields(kind, domain, title, body)
    if not err and scope == "workspace" and not workspace.strip():
        err = "Workspace is required when scope is 'workspace'."
    if err:
        return _render_entries(
            request,
            form_title=title, form_body=body, form_approve=approve,
            form_scope=scope, form_workspace=workspace,
            error=err, show_add=True,
        )

    entry = MemoryEntry(
        id="",
        kind=MemoryKind(kind),
        domain=domain,
        title=title.strip(),
        body=body,
        tags=[],
        approved=approve,
        approved_by=_author_from(request),
        repo_path="",
        scope=MemoryScope(scope) if scope in ("global", "workspace") else MemoryScope.GLOBAL,
        source=MemorySource.HUMAN,
        workspace=workspace.strip() if scope == "workspace" else "",
    )
    saved = _store().save(entry)
    return RedirectResponse(url=f"/entries/{saved.id}", status_code=303)


def _approve_ids(cur, ids: list[str], actor: str) -> int:
    """Approve each not-yet-approved id, logging an audit row. Returns count approved."""
    approved = 0
    for entry_id in ids:
        cur.execute(
            "UPDATE memory_entries SET approved = TRUE, approved_by = %s WHERE id = %s AND NOT approved",
            (actor, entry_id),
        )
        if cur.rowcount:
            approved += 1
            cur.execute(
                "INSERT INTO memory_audit_log (entry_id, action, actor) VALUES (%s, 'approve', %s)",
                (entry_id, actor),
            )
    return approved


@app.post("/entries/{entry_id}/approve")
def entry_approve(request: Request, entry_id: str):
    actor = _author_from(request)
    with _pool().connection() as conn, conn.cursor() as cur:
        _approve_ids(cur, [entry_id], actor)
    return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)


@app.post("/entries/approve-bulk")
def entries_approve_bulk(request: Request, ids: list[str] = Form(default=[])):
    """Approve many entries at once from the filtered Knowledge list."""
    if ids:
        actor = _author_from(request)
        with _pool().connection() as conn, conn.cursor() as cur:
            _approve_ids(cur, ids, actor)
    back = request.headers.get("referer") or "/entries"
    return RedirectResponse(url=back, status_code=303)


@app.post("/entries/{entry_id}/delete")
def entry_delete(entry_id: str):
    _store().delete(entry_id)
    return RedirectResponse(url="/entries", status_code=303)


@app.post("/entries/{entry_id}/rescope")
def entry_rescope(
    request: Request,
    entry_id: str,
    scope: str = Form("global"),
    workspace: str = Form(""),
):
    """Promote workspace → global, or move global → workspace."""
    if scope not in ("global", "workspace"):
        return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)
    ws = workspace.strip() if scope == "workspace" else ""
    if scope == "workspace" and not ws:
        return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)
    actor = _author_from(request)
    with _pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE memory_entries SET scope = %s::memory_scope, workspace = %s WHERE id = %s",
            (scope, ws, entry_id),
        )
        if cur.rowcount:
            cur.execute(
                "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, 'update', %s, %s::jsonb)",
                (entry_id, actor, json.dumps({"rescope": scope, "workspace": ws})),
            )
    return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)


def _render_entry_edit(
    request: Request,
    entry_id: str,
    *,
    form_title: str,
    form_body: str,
    error: str = "",
):
    entry = _fetch_one(
        "SELECT id FROM memory_entries WHERE id = %s",
        (entry_id,),
    )
    return TEMPLATES.TemplateResponse(
        request,
        "entry_edit.html",
        {
            "entry_id": entry_id,
            "entry_exists": entry is not None,
            "active": "entries",
            "error": error,
            "form_title": form_title,
            "form_body": form_body,
        },
    )


@app.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
def entry_edit_form(request: Request, entry_id: str):
    entry = _fetch_one(
        "SELECT title, body FROM memory_entries WHERE id = %s",
        (entry_id,),
    )
    if not entry:
        return _render_entry_edit(request, entry_id, form_title="", form_body="")
    return _render_entry_edit(
        request, entry_id,
        form_title=entry["title"],
        form_body=entry["body"],
    )


@app.post("/entries/{entry_id}/edit")
def entry_edit_submit(
    request: Request,
    entry_id: str,
    title: str = Form(""),
    body: str = Form(""),
):
    err = _validate_fields(_DEFAULT_KIND, _DEFAULT_DOMAIN, title, body)
    if err:
        return _render_entry_edit(
            request, entry_id,
            form_title=title, form_body=body,
            error=err,
        )

    actor = _author_from(request)
    with _pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE memory_entries SET title = %s, body = %s WHERE id = %s",
            (title.strip(), body, entry_id),
        )
        if cur.rowcount:
            cur.execute(
                "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, 'update', %s, %s::jsonb)",
                (entry_id, actor, '{"source":"web-edit"}'),
            )
    return RedirectResponse(url=f"/entries/{entry_id}", status_code=303)


@app.post("/me")
def set_author(name: str = Form(...)):
    """Sticky cookie so a team member doesn't retype their name on every form."""
    resp = RedirectResponse(url="/knowledge", status_code=303)
    resp.set_cookie("precept_author", name.strip()[:64], max_age=60 * 60 * 24 * 365)
    return resp


@app.get("/healthz")
def healthz():
    try:
        with _pool().connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
