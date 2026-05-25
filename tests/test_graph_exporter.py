"""Tests for graph exporters."""

from knowai.graph.cognitive_graph import CognitiveGraph
from knowai.graph.exporter import GraphExporter
from knowai.models.schema import ArchitecturePattern, ScanResult
from knowai.scanner.repo_scanner import RepoScanner


def _build_graph() -> CognitiveGraph:
    scan = ScanResult(
        repo_path="/tmp/test",
        language="typescript",
        framework="nextjs",
        architecture=ArchitecturePattern.CLEAN,
        domains=["payment", "auth", "webhook"],
    )
    g = CognitiveGraph()
    g.build(scan)
    return g


def test_react_flow_has_nodes_and_edges():
    g = _build_graph()
    result = GraphExporter.to_react_flow(g)
    assert "nodes" in result
    assert "edges" in result
    assert isinstance(result["nodes"], list)


def test_mermaid_starts_with_graph():
    g = _build_graph()
    result = GraphExporter.to_mermaid(g)
    assert result.startswith("graph LR")


def test_dot_starts_with_digraph():
    g = _build_graph()
    result = GraphExporter.to_dot(g)
    assert result.startswith("digraph")


def test_react_flow_node_has_style():
    g = _build_graph()
    result = GraphExporter.to_react_flow(g)
    if result["nodes"]:
        assert "style" in result["nodes"][0]
        assert "background" in result["nodes"][0]["style"]
