"""Detects team conventions from code patterns."""

from __future__ import annotations

from pathlib import Path

from knowai.models.schema import ArchitecturePattern, Convention, ScanResult


class ConventionDetector:
    def __init__(self, root: Path, scan: ScanResult) -> None:
        self.root = root
        self.scan = scan

    def detect(self) -> list[Convention]:
        conventions: list[Convention] = []
        conventions.extend(self._naming_conventions())
        conventions.extend(self._import_conventions())
        conventions.extend(self._architecture_conventions())
        conventions.extend(self._lint_conventions())
        conventions.extend(self._test_conventions())
        return conventions

    def _naming_conventions(self) -> list[Convention]:
        result: list[Convention] = []
        ts_files = list(self.root.rglob("*.ts")) + list(self.root.rglob("*.tsx"))
        ts_files = [f for f in ts_files if not any(p in str(f) for p in ["node_modules", ".next", "generated"])]

        if ts_files[:20]:
            component_files = [f for f in ts_files if f.suffix == ".tsx"]
            if component_files:
                pascal = sum(1 for f in component_files if f.stem[0].isupper())
                camel = sum(1 for f in component_files if f.stem[0].islower())
                if pascal > camel:
                    result.append(Convention(
                        name="component_naming",
                        rule="React component files must use PascalCase naming",
                        examples=["UserCard.tsx", "PaymentForm.tsx"],
                    ))

        py_files = list(self.root.rglob("*.py"))
        py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        if py_files:
            result.append(Convention(
                name="python_naming",
                rule="Python files must use snake_case naming",
                examples=["user_service.py", "payment_repository.py"],
            ))

        return result

    def _import_conventions(self) -> list[Convention]:
        result: list[Convention] = []

        # Check for path aliases in tsconfig
        tsconfig = self.root / "tsconfig.json"
        if tsconfig.exists():
            try:
                import json
                cfg = json.loads(tsconfig.read_text())
                paths = cfg.get("compilerOptions", {}).get("paths", {})
                if paths:
                    aliases = list(paths.keys())[:3]
                    result.append(Convention(
                        name="ts_path_aliases",
                        rule=f"Use TypeScript path aliases for imports, not relative paths beyond 2 levels. Configured aliases: {aliases}",
                        examples=[f"import x from '{aliases[0].rstrip('*')}foo'" if aliases else "import x from '@/components/foo'"],
                    ))
            except Exception:
                pass

        # Check for generated client usage
        if self.scan.api_clients:
            result.append(Convention(
                name="api_client_usage",
                rule=f"Always import API calls from the generated client ({self.scan.api_clients[0]}), never use raw fetch/axios",
                enforced=True,
            ))

        return result

    def _architecture_conventions(self) -> list[Convention]:
        result: list[Convention] = []

        if self.scan.architecture == ArchitecturePattern.CLEAN:
            result.extend([
                Convention(
                    name="clean_arch_dependency_rule",
                    rule="Dependencies must point inward only: infrastructure → application → domain. Domain has zero external deps.",
                    enforced=True,
                ),
                Convention(
                    name="clean_arch_no_logic_in_controllers",
                    rule="Controllers/handlers must not contain business logic — delegate to use cases/services",
                    enforced=True,
                    examples=["controller calls userService.create(dto), not raw DB calls"],
                ),
            ])

        if self.scan.architecture == ArchitecturePattern.DDD:
            result.extend([
                Convention(
                    name="ddd_aggregate_root",
                    rule="All state mutations must go through the Aggregate Root, not child entities directly",
                    enforced=True,
                ),
                Convention(
                    name="ddd_no_anemic_domain",
                    rule="Domain entities must contain business logic, not be plain data bags",
                    enforced=True,
                ),
            ])

        if self.scan.architecture in (ArchitecturePattern.CLEAN, ArchitecturePattern.LAYERED):
            result.append(Convention(
                name="repository_pattern",
                rule="Database access must go through Repository interfaces — no raw ORM calls in services",
                enforced=True,
            ))

        return result

    def _lint_conventions(self) -> list[Convention]:
        result: list[Convention] = []
        if (self.root / ".eslintrc.js").exists() or (self.root / ".eslintrc.json").exists() or (self.root / "eslint.config.js").exists():
            result.append(Convention(name="eslint", rule="Code must pass ESLint rules configured in this project", enforced=True))
        if (self.root / "ruff.toml").exists() or (self.root / "pyproject.toml").exists():
            text = (self.root / "pyproject.toml").read_text() if (self.root / "pyproject.toml").exists() else ""
            if "[tool.ruff]" in text:
                result.append(Convention(name="ruff", rule="Python code must pass ruff lint and format checks", enforced=True))
        if (self.root / ".prettierrc").exists() or (self.root / "prettier.config.js").exists():
            result.append(Convention(name="prettier", rule="Code must be formatted with Prettier", enforced=True))
        return result

    def _test_conventions(self) -> list[Convention]:
        result: list[Convention] = []
        has_jest = (self.root / "jest.config.ts").exists() or (self.root / "jest.config.js").exists()
        has_vitest = (self.root / "vitest.config.ts").exists()
        has_pytest = (self.root / "pytest.ini").exists() or (
            (self.root / "pyproject.toml").exists()
            and "[tool.pytest" in (self.root / "pyproject.toml").read_text()
        )

        if has_jest:
            result.append(Convention(name="test_framework", rule="Use Jest for testing. Test files must end in .spec.ts or .test.ts"))
        if has_vitest:
            result.append(Convention(name="test_framework", rule="Use Vitest for testing. Test files must end in .spec.ts or .test.ts"))
        if has_pytest:
            result.append(Convention(name="test_framework", rule="Use pytest. Test files must be named test_*.py"))

        # Check for co-located vs centralized tests
        spec_count = sum(1 for _ in self.root.rglob("*.spec.ts"))
        centralized = (self.root / "tests").exists() or (self.root / "__tests__").exists()
        if spec_count > 5:
            result.append(Convention(name="test_location", rule="Tests are co-located with source files (*.spec.ts alongside source)"))
        elif centralized:
            result.append(Convention(name="test_location", rule="Tests live in the centralized /tests directory, not co-located"))

        return result
