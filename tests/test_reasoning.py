"""Tests for the reasoning layer."""

import pytest

from knowlyx.graph.cognitive_graph import CognitiveGraph
from knowlyx.models.schema import AIDecision, ArchitecturePattern, ScanResult
from knowlyx.reasoning.engine import ReasoningEngine
from knowlyx.reasoning.intent_analyzer import IntentAnalyzer
from knowlyx.reasoning.risk_scorer import RiskScorer


def _make_scan(**kwargs) -> ScanResult:
    defaults = dict(
        repo_path="/tmp/test",
        language="typescript",
        framework="nextjs",
        architecture=ArchitecturePattern.CLEAN,
        domains=["payment", "auth", "user", "audit", "webhook"],
    )
    defaults.update(kwargs)
    return ScanResult(**defaults)


def test_intent_payment():
    scan = _make_scan()
    result = IntentAnalyzer(scan).analyze("fix payment scan 501 error")
    assert result.detected_domain == "payment"
    assert result.detected_action == "fix"
    assert "audit" in result.affected_areas


def test_intent_otp():
    scan = _make_scan()
    result = IntentAnalyzer(scan).analyze("เพิ่ม OTP login")
    assert result.detected_domain in ("auth", "otp", "general")
    assert len(result.inferred_requirements) > 0


def test_risk_critical_delete():
    scan = _make_scan()
    graph = CognitiveGraph()
    graph.build(scan)
    engine = ReasoningEngine(scan, graph)
    report = engine.analyze("delete all payment records from production database drop table")
    assert report.risk.decision in (AIDecision.REJECT, AIDecision.ASK)
    assert report.risk.level.value in ("critical", "high")


def test_risk_low_read():
    scan = _make_scan()
    graph = CognitiveGraph()
    graph.build(scan)
    engine = ReasoningEngine(scan, graph)
    report = engine.analyze("show me the list of users")
    assert report.risk.decision == AIDecision.PROCEED


def test_full_report_has_plan():
    scan = _make_scan()
    graph = CognitiveGraph()
    graph.build(scan)
    engine = ReasoningEngine(scan, graph)
    report = engine.analyze("add OTP login")
    assert len(report.suggested_plan) > 0
