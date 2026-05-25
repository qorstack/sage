"""
Graph exporter — converts cognitive graphs to formats suitable for visualization.

Supported formats:
  - React Flow JSON  (nodes + edges ready for <ReactFlow> component)
  - DOT              (Graphviz, for static diagrams)
  - Mermaid          (for markdown embedding)
  - JSON summary     (lightweight, for API responses)
"""

from __future__ import annotations

from typing import Any

from knowai.graph.cognitive_graph import CognitiveGraph
from knowai.workspace.multi_scanner import WorkspaceScanResult

# ------------------------------------------------------------------
# Color palette per node kind
# ------------------------------------------------------------------
_KIND_STYLE: dict[str, dict[str, str]] = {
    "domain":      {"background": "#7c3aed", "color": "#fff", "border": "#5b21b6"},
    "component":   {"background": "#0891b2", "color": "#fff", "border": "#0e7490"},
    "hook":        {"background": "#0284c7", "color": "#fff", "border": "#0369a1"},
    "util":        {"background": "#6b7280", "color": "#fff", "border": "#4b5563"},
    "service":     {"background": "#d97706", "color": "#fff", "border": "#b45309"},
    "convention":  {"background": "#dc2626", "color": "#fff", "border": "#b91c1c"},
    "repo":        {"background": "#16a34a", "color": "#fff", "border": "#15803d"},
}

_ROLE_STYLE: dict[str, dict[str, str]] = {
    "backend":  {"background": "#1d4ed8", "color": "#fff", "border": "#1e40af"},
    "frontend": {"background": "#7c3aed", "color": "#fff", "border": "#6d28d9"},
    "worker":   {"background": "#c2410c", "color": "#fff", "border": "#9a3412"},
    "gateway":  {"background": "#0f766e", "color": "#fff", "border": "#0d9488"},
    "shared":   {"background": "#475569", "color": "#fff", "border": "#334155"},
}


class GraphExporter:
    # ------------------------------------------------------------------
    # Single-repo cognitive graph
    # ------------------------------------------------------------------

    @staticmethod
    def to_react_flow(graph: CognitiveGraph, layout: str = "dagre") -> dict[str, Any]:
        """Export a single-repo CognitiveGraph to React Flow format."""
        nodes: list[dict] = []
        edges: list[dict] = []

        for i, (node_id, data) in enumerate(graph.g.nodes(data=True)):
            kind = data.get("kind", "util")
            style = _KIND_STYLE.get(kind, _KIND_STYLE["util"])
            nodes.append({
                "id": node_id,
                "type": "default",
                "data": {
                    "label": data.get("name", node_id),
                    "kind": kind,
                    "path": data.get("path", ""),
                    "rule": data.get("rule", ""),
                    "tags": data.get("tags", []),
                },
                "style": {
                    "background": style["background"],
                    "color": style["color"],
                    "border": f"2px solid {style['border']}",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "fontSize": "12px",
                },
                "position": {"x": (i % 8) * 180, "y": (i // 8) * 120},
            })

        for j, (src, tgt, data) in enumerate(graph.g.edges(data=True)):
            edges.append({
                "id": f"e{j}",
                "source": src,
                "target": tgt,
                "label": data.get("rel", ""),
                "animated": data.get("rel") == "impacts",
                "style": {"stroke": "#94a3b8"},
                "labelStyle": {"fontSize": "10px", "fill": "#64748b"},
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "meta": {
                "layout": layout,
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

    @staticmethod
    def to_workspace_react_flow(ws: WorkspaceScanResult) -> dict[str, Any]:
        """Export cross-repo workspace graph to React Flow format."""
        g = ws.cross_repo_graph
        nodes: list[dict] = []
        edges: list[dict] = []

        for i, (node_id, data) in enumerate(g.nodes(data=True)):
            role = data.get("role", "unknown")
            style = _ROLE_STYLE.get(role, {"background": "#475569", "color": "#fff", "border": "#334155"})
            nodes.append({
                "id": node_id,
                "type": "default",
                "data": {
                    "label": node_id,
                    "role": role,
                    "language": data.get("language", ""),
                    "framework": data.get("framework", ""),
                    "domains": data.get("domains", []),
                    "critical": data.get("critical", False),
                },
                "style": {
                    "background": style["background"],
                    "color": style["color"],
                    "border": f"2px solid {style['border']}",
                    "borderRadius": "12px",
                    "padding": "12px 16px",
                    "fontSize": "13px",
                    "fontWeight": "bold",
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.3)" if data.get("critical") else "none",
                },
                "position": {"x": (i % 4) * 280, "y": (i // 4) * 200},
            })

        for j, (src, tgt, data) in enumerate(g.edges(data=True)):
            rel = data.get("rel", "")
            edges.append({
                "id": f"e{j}",
                "source": src,
                "target": tgt,
                "label": rel,
                "animated": rel in ("api", "api_inferred"),
                "style": {
                    "stroke": "#f59e0b" if "inferred" in rel else "#94a3b8",
                    "strokeDasharray": "5,5" if "inferred" in rel else "none",
                },
                "markerEnd": {"type": "arrowclosed"},
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "meta": {
                "workspace": ws.workspace_name,
                "repo_count": len(ws.repos),
                "layout": "dagre",
            },
        }

    # ------------------------------------------------------------------
    # DOT (Graphviz)
    # ------------------------------------------------------------------

    @staticmethod
    def to_dot(graph: CognitiveGraph, title: str = "knowai") -> str:
        lines = [f'digraph "{title}" {{', '  rankdir=LR;', '  node [shape=box, style=filled, fontsize=10];']
        _DOT_COLORS = {"domain": "mediumpurple", "component": "skyblue", "hook": "steelblue", "util": "lightgray", "service": "orange", "convention": "tomato"}
        for node_id, data in graph.g.nodes(data=True):
            kind = data.get("kind", "util")
            color = _DOT_COLORS.get(kind, "lightgray")
            label = data.get("name", node_id).replace('"', '\\"')
            lines.append(f'  "{node_id}" [label="{label}", fillcolor="{color}"];')
        for src, tgt, data in graph.g.edges(data=True):
            rel = data.get("rel", "")
            lines.append(f'  "{src}" -> "{tgt}" [label="{rel}"];')
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def workspace_to_dot(ws: WorkspaceScanResult) -> str:
        g = ws.cross_repo_graph
        lines = [f'digraph "{ws.workspace_name}" {{', '  rankdir=LR;', '  node [shape=box, style=filled, fontsize=12, fontweight=bold];']
        _ROLE_COLORS = {"backend": "steelblue", "frontend": "mediumpurple", "worker": "coral", "gateway": "teal", "shared": "lightgray"}
        for node_id, data in g.nodes(data=True):
            color = _ROLE_COLORS.get(data.get("role", ""), "lightgray")
            extra = ' peripheries=2' if data.get("critical") else ''
            lines.append(f'  "{node_id}" [label="{node_id}\\n({data.get("role","")})\\n{data.get("framework","")}", fillcolor="{color}"{extra}];')
        for src, tgt, data in g.edges(data=True):
            style = 'dashed' if 'inferred' in data.get("rel", "") else 'solid'
            lines.append(f'  "{src}" -> "{tgt}" [label="{data.get("rel","")}", style="{style}"];')
        lines.append("}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Mermaid
    # ------------------------------------------------------------------

    @staticmethod
    def to_mermaid(graph: CognitiveGraph) -> str:
        lines = ["graph LR"]
        for node_id, data in graph.g.nodes(data=True):
            label = data.get("name", node_id)
            safe_id = node_id.replace(":", "_").replace("/", "_").replace(".", "_")
            lines.append(f'  {safe_id}["{label}"]')
        for src, tgt, data in graph.g.edges(data=True):
            safe_src = src.replace(":", "_").replace("/", "_").replace(".", "_")
            safe_tgt = tgt.replace(":", "_").replace("/", "_").replace(".", "_")
            rel = data.get("rel", "")
            lines.append(f'  {safe_src} -->|"{rel}"| {safe_tgt}')
        return "\n".join(lines)

    @staticmethod
    def workspace_to_mermaid(ws: WorkspaceScanResult) -> str:
        g = ws.cross_repo_graph
        lines = ["graph LR"]
        for node_id, data in g.nodes(data=True):
            shape_open, shape_close = ("((", "))") if data.get("critical") else ("[", "]")
            lines.append(f'  {node_id}{shape_open}"{node_id}<br/>{data.get("role","")}{shape_close}')
        for src, tgt, data in g.edges(data=True):
            rel = data.get("rel", "")
            arrow = "-.->|" if "inferred" in rel else "-->|"
            lines.append(f'  {src} {arrow}"{rel}"| {tgt}')
        return "\n".join(lines)
