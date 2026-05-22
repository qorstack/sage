"""Tests for the CodeValidator (AI self-review)."""

from __future__ import annotations

import pytest

from knowlyx.models.schema import (
    ArchitecturePattern,
    Convention,
    ReusableAsset,
    ScanResult,
)
from knowlyx.validation.code_validator import CodeValidator, Severity


@pytest.fixture
def py_scan(tmp_path):
    return ScanResult(
        repo_path=str(tmp_path),
        language="python",
        framework="fastapi",
        architecture=ArchitecturePattern.LAYERED,
        forbidden_patterns=["console.log usage"],
        reusable_assets=[
            ReusableAsset(
                name="formatCurrency",
                asset_type="util",
                path="src/utils/money.ts",
                tags=["billing"],
            ),
        ],
        conventions=[
            Convention(name="no-print", rule="do not use print() in production", enforced=True),
        ],
    )


@pytest.fixture
def ts_scan(tmp_path):
    return ScanResult(
        repo_path=str(tmp_path),
        language="typescript",
        framework="nextjs",
        architecture=ArchitecturePattern.MODULAR_MONOLITH,
        reusable_assets=[
            ReusableAsset(
                name="useCheckout",
                asset_type="hook",
                path="src/hooks/useCheckout.ts",
                tags=["checkout"],
            ),
        ],
    )


def test_validator_passes_clean_code(py_scan):
    code = "from pathlib import Path\n\ndef ok():\n    return Path('.').name\n"
    report = CodeValidator(py_scan).validate(code, language="python")
    assert report.passed is True
    assert not report.has_blockers


def test_validator_flags_hardcoded_secrets(py_scan):
    code = 'STRIPE = "sk_live_abcdef1234567890ABCDEF"\n'
    report = CodeValidator(py_scan).validate(code, language="python")
    assert report.has_blockers
    assert any("secret" in v.rule for v in report.violations)


def test_validator_flags_duplicate_asset(ts_scan):
    code = "function useCheckout() {\n  return null\n}\n"
    report = CodeValidator(ts_scan).validate(code, language="typescript")
    assert any(v.rule == "duplicate_asset" for v in report.violations)


def test_validator_flags_hallucinated_python_import(py_scan):
    code = "from totally_made_up_package import widget\n"
    report = CodeValidator(py_scan).validate(code, language="python")
    assert report.has_blockers
    assert any(v.rule == "hallucinated_import" for v in report.violations)


def test_validator_does_not_flag_stdlib(py_scan):
    code = "import json\nimport os\nfrom datetime import datetime\n"
    report = CodeValidator(py_scan).validate(code, language="python")
    assert not any(v.rule == "hallucinated_import" for v in report.violations)


def test_validator_flags_forbidden_pattern_keyword(py_scan):
    # forbidden_patterns lists "console.log usage"
    code = "function x() {\n  console.log('hi')\n}\n"
    report = CodeValidator(py_scan).validate(code, language="typescript")
    assert any("console.log" in v.message or "forbidden" in v.rule for v in report.violations)


def test_validator_report_to_dict_shape(py_scan):
    code = "print('debug')\n"
    report = CodeValidator(py_scan).validate(code, language="python")
    d = report.to_dict()
    assert {"passed", "has_blockers", "violation_count", "violations"} <= d.keys()
    if d["violations"]:
        v0 = d["violations"][0]
        assert {"severity", "rule", "message"} <= v0.keys()
