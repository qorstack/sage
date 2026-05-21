"""Scans a repository and builds a raw understanding of its structure."""

from __future__ import annotations

import json
import re
from pathlib import Path

from knowlyx.models.schema import ArchitecturePattern, ScanResult
from knowlyx.scanner.asset_detector import AssetDetector
from knowlyx.scanner.convention_detector import ConventionDetector

_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
    "build", ".next", ".nuxt", "coverage", ".pytest_cache", ".ruff_cache",
}


class RepoScanner:
    def __init__(self, repo_path: str | Path) -> None:
        self.root = Path(repo_path).resolve()

    def scan(self) -> ScanResult:
        result = ScanResult(repo_path=str(self.root))
        result.language, result.framework = self._detect_stack()
        result.architecture = self._detect_architecture()
        result.domains = self._detect_domains()
        result.api_clients = self._detect_api_clients()
        result.forbidden_patterns = self._detect_forbidden_patterns(result)

        convention_detector = ConventionDetector(self.root, result)
        result.conventions = convention_detector.detect()

        asset_detector = AssetDetector(self.root, result)
        result.reusable_assets = asset_detector.detect()

        result.metadata = {
            "total_files": self._count_files(),
            "has_docker": (self.root / "Dockerfile").exists() or (self.root / "docker-compose.yml").exists(),
            "has_ci": any((self.root / d).exists() for d in [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"]),
            "monorepo": self._is_monorepo(),
        }
        return result

    # ------------------------------------------------------------------
    # Stack detection
    # ------------------------------------------------------------------

    def _detect_stack(self) -> tuple[str, str]:
        if (self.root / "pyproject.toml").exists() or (self.root / "requirements.txt").exists():
            return self._python_framework()
        if (self.root / "package.json").exists():
            return self._node_framework()
        if (self.root / "go.mod").exists():
            return "go", "go"
        if (self.root / "Cargo.toml").exists():
            return "rust", "rust"
        if (self.root / "pom.xml").exists() or (self.root / "build.gradle").exists():
            return "java", "spring"
        return "unknown", "unknown"

    def _python_framework(self) -> tuple[str, str]:
        deps = self._read_python_deps()
        if "fastapi" in deps:
            return "python", "fastapi"
        if "django" in deps:
            return "python", "django"
        if "flask" in deps:
            return "python", "flask"
        return "python", "python"

    def _node_framework(self) -> tuple[str, str]:
        pkg = self._read_package_json()
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "next" in deps:
            return "typescript" if (self.root / "tsconfig.json").exists() else "javascript", "nextjs"
        if "react" in deps:
            return "typescript" if (self.root / "tsconfig.json").exists() else "javascript", "react"
        if "express" in deps:
            return "typescript" if (self.root / "tsconfig.json").exists() else "javascript", "express"
        if "nestjs" in deps or "@nestjs/core" in deps:
            return "typescript", "nestjs"
        return "javascript", "node"

    # ------------------------------------------------------------------
    # Architecture detection
    # ------------------------------------------------------------------

    def _detect_architecture(self) -> ArchitecturePattern:
        dirs = {p.name for p in self.root.iterdir() if p.is_dir() and p.name not in _IGNORE_DIRS}

        # Clean architecture signals
        if {"domain", "application", "infrastructure", "presentation"} & dirs:
            return ArchitecturePattern.CLEAN
        if {"domain", "usecase", "repository", "controller"} & dirs:
            return ArchitecturePattern.CLEAN
        if {"core", "adapters", "ports"} & dirs:
            return ArchitecturePattern.CLEAN

        # DDD signals
        if {"aggregates", "entities", "value_objects", "events"} & dirs:
            return ArchitecturePattern.DDD
        if self._has_bounded_contexts():
            return ArchitecturePattern.DDD

        # Modular monolith
        src_dirs = list((self.root / "src").iterdir()) if (self.root / "src").exists() else []
        module_dirs = [d for d in src_dirs if d.is_dir() and d.name not in _IGNORE_DIRS]
        if len(module_dirs) >= 3 and all(
            any((m / sub).exists() for sub in ["controller", "service", "model", "route", "handler", "index.ts", "index.py"])
            for m in module_dirs
        ):
            return ArchitecturePattern.MODULAR_MONOLITH

        # Layered
        if {"controllers", "services", "models", "routes"} & dirs or {"controller", "service", "model", "repository"} & dirs:
            return ArchitecturePattern.LAYERED

        return ArchitecturePattern.UNKNOWN

    def _has_bounded_contexts(self) -> bool:
        src = self.root / "src"
        if not src.exists():
            return False
        for d in src.iterdir():
            if d.is_dir() and (d / "domain").exists():
                return True
        return False

    # ------------------------------------------------------------------
    # Domain detection
    # ------------------------------------------------------------------

    def _detect_domains(self) -> list[str]:
        domains: set[str] = set()
        _DOMAIN_KEYWORDS = {
            "auth", "payment", "order", "user", "product", "notification",
            "report", "admin", "invoice", "shipping", "inventory", "search",
            "cart", "checkout", "subscription", "webhook", "audit", "worker",
        }
        for path in self._walk():
            parts = {p.lower() for p in path.parts}
            found = parts & _DOMAIN_KEYWORDS
            domains.update(found)
        return sorted(domains)

    # ------------------------------------------------------------------
    # API client detection
    # ------------------------------------------------------------------

    def _detect_api_clients(self) -> list[str]:
        clients: list[str] = []
        generated_markers = ["generated", "gen", "openapi", "swagger-client", "__generated__"]
        for d in self.root.rglob("*"):
            if d.is_dir() and d.name.lower() in generated_markers:
                clients.append(str(d.relative_to(self.root)))
        return clients

    # ------------------------------------------------------------------
    # Forbidden patterns
    # ------------------------------------------------------------------

    def _detect_forbidden_patterns(self, result: ScanResult) -> list[str]:
        patterns: list[str] = []
        if result.api_clients:
            patterns.append("Direct fetch/axios calls are forbidden — use the generated API client")
        if result.architecture in (ArchitecturePattern.CLEAN, ArchitecturePattern.DDD):
            patterns.append("Business logic must not live in controllers/handlers")
            patterns.append("Infrastructure concerns must not leak into domain layer")
        if result.language in ("typescript", "javascript"):
            if (self.root / "src" / "generated").exists() or any("generated" in str(p) for p in self.root.rglob("*.ts") if "generated" in str(p)):
                patterns.append("Never manually edit files inside generated/ directories")
        return patterns

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _walk(self):
        for path in self.root.rglob("*"):
            if any(part in _IGNORE_DIRS for part in path.parts):
                continue
            if path.is_file():
                yield path.relative_to(self.root)

    def _count_files(self) -> int:
        return sum(1 for _ in self._walk())

    def _is_monorepo(self) -> bool:
        return (
            (self.root / "pnpm-workspace.yaml").exists()
            or (self.root / "lerna.json").exists()
            or (self.root / "nx.json").exists()
            or (self.root / "turbo.json").exists()
            or (self.root / "packages").exists()
            or (self.root / "apps").exists()
        )

    def _read_package_json(self) -> dict:
        pkg = self.root / "package.json"
        if pkg.exists():
            try:
                return json.loads(pkg.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _read_python_deps(self) -> set[str]:
        deps: set[str] = set()
        for f in ["requirements.txt", "requirements-dev.txt"]:
            fp = self.root / f
            if fp.exists():
                for line in fp.read_text().splitlines():
                    m = re.match(r"^([a-zA-Z0-9_-]+)", line.strip())
                    if m:
                        deps.add(m.group(1).lower())
        toml = self.root / "pyproject.toml"
        if toml.exists():
            text = toml.read_text()
            for m in re.finditer(r'"([a-zA-Z0-9_-]+)>=', text):
                deps.add(m.group(1).lower())
        return deps
