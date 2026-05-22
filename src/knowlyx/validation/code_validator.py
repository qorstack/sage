"""
Validate AI-generated code BEFORE it gets written to disk.

The MCP tool `validate_generated_code` is the gate — AI calls it with
the code it's about to write, gets back violations + suggestions, and
should fix them in-memory before calling Write/Edit.

This is rule-based, fast, and language-agnostic where possible.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from knowlyx.models.schema import ScanResult


class Severity(str, Enum):
    BLOCK = "block"      # must fix before writing
    WARN = "warn"        # surface but don't block
    INFO = "info"        # FYI


@dataclass
class Violation:
    severity: Severity
    rule: str
    message: str
    suggestion: str = ""
    line_hint: int | None = None


@dataclass
class ValidationReport:
    passed: bool
    violations: list[Violation] = field(default_factory=list)
    suggestions_count: int = 0

    @property
    def has_blockers(self) -> bool:
        return any(v.severity == Severity.BLOCK for v in self.violations)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "has_blockers": self.has_blockers,
            "violation_count": len(self.violations),
            "violations": [
                {
                    "severity": v.severity.value,
                    "rule": v.rule,
                    "message": v.message,
                    "suggestion": v.suggestion,
                    "line_hint": v.line_hint,
                }
                for v in self.violations
            ],
        }


_IMPORT_PATTERNS = {
    "typescript": [
        re.compile(r"""(?:^|\n)\s*import\s+(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]"""),
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "python": [
        re.compile(r"""(?:^|\n)\s*from\s+([\w\.]+)\s+import\s+"""),
        re.compile(r"""(?:^|\n)\s*import\s+([\w\.]+)"""),
    ],
}


class CodeValidator:
    def __init__(self, scan: ScanResult) -> None:
        self.scan = scan
        self._asset_names = {a.name.lower(): a for a in scan.reusable_assets}
        self._asset_paths = {a.path.replace("\\", "/").lower() for a in scan.reusable_assets}

    def validate(self, code: str, language: str = "") -> ValidationReport:
        violations: list[Violation] = []
        lang = (language or self.scan.language or "").lower()

        violations.extend(self._check_forbidden_patterns(code))
        violations.extend(self._check_hallucinated_imports(code, lang))
        violations.extend(self._check_duplicate_assets(code))
        violations.extend(self._check_convention_violations(code))
        violations.extend(self._check_secrets(code))

        return ValidationReport(
            passed=not any(v.severity == Severity.BLOCK for v in violations),
            violations=violations,
            suggestions_count=sum(1 for v in violations if v.suggestion),
        )

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _check_forbidden_patterns(self, code: str) -> list[Violation]:
        out: list[Violation] = []
        for pattern in self.scan.forbidden_patterns:
            # forbidden_patterns are descriptive strings — pick the meaningful keyword
            key = self._extract_keyword(pattern)
            if key and key in code:
                out.append(Violation(
                    severity=Severity.BLOCK,
                    rule=f"forbidden:{key}",
                    message=f"Code uses forbidden pattern: {pattern}",
                    suggestion=f"Remove or replace '{key}' — see project conventions",
                ))
        return out

    def _check_hallucinated_imports(self, code: str, lang: str) -> list[Violation]:
        out: list[Violation] = []
        patterns = _IMPORT_PATTERNS.get(lang, [])
        if not patterns:
            return out
        for pat in patterns:
            for match in pat.finditer(code):
                imp = match.group(1)
                if self._is_likely_hallucination(imp, lang):
                    suggestion = self._suggest_existing(imp)
                    out.append(Violation(
                        severity=Severity.BLOCK,
                        rule="hallucinated_import",
                        message=f"Import path '{imp}' not found in repo or known stdlib/deps",
                        suggestion=suggestion,
                    ))
        return out

    def _check_duplicate_assets(self, code: str) -> list[Violation]:
        """If new code defines a name that already exists as a reusable asset, suggest reuse."""
        out: list[Violation] = []
        for match in re.finditer(r"(?:function|const|class|def)\s+(\w+)", code):
            name = match.group(1)
            existing = self._asset_names.get(name.lower())
            if existing and existing.name != name:
                continue
            if existing:
                out.append(Violation(
                    severity=Severity.WARN,
                    rule="duplicate_asset",
                    message=f"'{name}' already exists at {existing.path}",
                    suggestion=f"Import from {existing.path} instead of redefining",
                ))
        return out

    def _check_convention_violations(self, code: str) -> list[Violation]:
        out: list[Violation] = []
        for conv in self.scan.conventions:
            if not conv.enforced:
                continue
            keyword = self._extract_keyword(conv.rule)
            if not keyword:
                continue
            # convention encoded as "must use X" / "do not use Y" — heuristic
            text = conv.rule.lower()
            if any(neg in text for neg in ("don't use", "do not use", "forbidden", "avoid")):
                if keyword in code:
                    out.append(Violation(
                        severity=Severity.BLOCK,
                        rule=f"convention:{conv.name}",
                        message=f"Violates convention '{conv.name}': {conv.rule}",
                    ))
        return out

    def _check_secrets(self, code: str) -> list[Violation]:
        out: list[Violation] = []
        patterns = [
            (r"""['"](?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}['"]""", "stripe-key"),
            (r"""['"]AKIA[0-9A-Z]{16}['"]""", "aws-access-key"),
            (r"""['"]ghp_[A-Za-z0-9]{36}['"]""", "github-pat"),
            (r"""(?i)password\s*=\s*['"][^'"]{6,}['"]""", "hardcoded-password"),
        ]
        for pat, name in patterns:
            if re.search(pat, code):
                out.append(Violation(
                    severity=Severity.BLOCK,
                    rule=f"secret:{name}",
                    message=f"Possible hardcoded {name} detected",
                    suggestion="Use environment variables or a secrets manager",
                ))
        return out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_likely_hallucination(self, imp: str, lang: str) -> bool:
        if not imp or imp.startswith("."):
            return False
        # Relative or package-internal — assume valid
        if lang == "typescript":
            if imp.startswith("@/") or imp.startswith("~/"):
                # project alias — check if any asset path matches
                tail = imp.split("/", 1)[1] if "/" in imp else ""
                if tail and any(tail.lower() in p for p in self._asset_paths):
                    return False
                # alias to something with no matching asset → suspicious
                return True
            # known npm / scoped packages — assume valid (we can't enumerate them)
            return False
        if lang == "python":
            top = imp.split(".")[0]
            if top in _STDLIB:
                return False
            # local repo modules — try to find a file
            repo = Path(self.scan.repo_path)
            candidate = repo / Path(*top.split("."))
            if candidate.exists() or candidate.with_suffix(".py").exists():
                return False
            return True
        return False

    def _suggest_existing(self, imp: str) -> str:
        tail = imp.rsplit("/", 1)[-1].rsplit(".", 1)[-1].lower()
        for name, asset in self._asset_names.items():
            if name in tail or tail in name:
                return f"Use existing {asset.asset_type} '{asset.name}' at {asset.path}"
        return ""

    @staticmethod
    def _extract_keyword(text: str) -> str:
        # try to pull the most distinctive token (CamelCase, snake_case, dotted)
        m = re.search(r"([A-Za-z_][A-Za-z0-9_\.]{2,})", text)
        return m.group(1) if m else ""


_STDLIB = {
    "os", "sys", "re", "json", "pathlib", "typing", "datetime", "enum",
    "dataclasses", "abc", "collections", "itertools", "functools", "hashlib",
    "uuid", "time", "logging", "asyncio", "subprocess", "shutil", "io",
    "math", "random", "string", "tempfile", "argparse", "contextlib",
    "warnings", "copy", "weakref", "inspect", "importlib", "pkgutil",
    "ast", "textwrap", "base64", "secrets", "urllib", "http", "socket",
    "threading", "multiprocessing", "queue", "concurrent", "decimal",
    "fractions", "statistics", "csv", "pickle", "sqlite3", "xml", "html",
    "email", "mimetypes", "platform", "errno", "ctypes", "struct",
    "__future__",
}
