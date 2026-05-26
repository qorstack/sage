"""Detects reusable assets: components, hooks, utils, services, types."""

from __future__ import annotations

import re
from pathlib import Path

from knowai.models.schema import ReusableAsset, ScanResult
from knowai.scanner._safe_walk import safe_rglob

_IGNORE = {"node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", "generated", "__generated__"}


class AssetDetector:
    def __init__(self, root: Path, scan: ScanResult) -> None:
        self.root = root
        self.scan = scan

    def detect(self) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []
        assets.extend(self._detect_components())
        assets.extend(self._detect_hooks())
        assets.extend(self._detect_utils())
        assets.extend(self._detect_services())
        assets.extend(self._detect_python_assets())
        return assets

    def _detect_components(self) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []
        component_dirs = ["components", "ui", "shared", "common"]
        for dir_name in component_dirs:
            for comp_dir in safe_rglob(self.root, dir_name):
                if not comp_dir.is_dir():
                    continue
                for f in comp_dir.glob("*.tsx"):
                    if f.stem.startswith("_") or f.stem == "index":
                        continue
                    exports = self._extract_ts_exports(f)
                    assets.append(ReusableAsset(
                        name=f.stem,
                        asset_type="component",
                        path=str(f.relative_to(self.root)),
                        description=f"React component. Exports: {', '.join(exports[:3]) or f.stem}",
                        tags=self._infer_tags(f.stem),
                    ))
        return assets

    def _detect_hooks(self) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []
        hook_dirs = ["hooks", "lib/hooks", "src/hooks"]
        for dir_name in hook_dirs:
            hook_dir = self.root / dir_name
            if not hook_dir.exists():
                # try rglob
                for found in safe_rglob(self.root, dir_name):
                    if found.is_dir():
                        hook_dir = found
                        break
                else:
                    continue

            for f in hook_dir.glob("use*.ts*"):
                if any(p in str(f) for p in _IGNORE):
                    continue
                assets.append(ReusableAsset(
                    name=f.stem,
                    asset_type="hook",
                    path=str(f.relative_to(self.root)),
                    description="Custom React hook",
                    tags=self._infer_tags(f.stem),
                ))

        # also pick up any use*.ts files outside hook dirs
        for f in safe_rglob(self.root, "use*.ts*"):
            rel = str(f.relative_to(self.root))
            if not any(a.path == rel for a in assets):
                assets.append(ReusableAsset(
                    name=f.stem,
                    asset_type="hook",
                    path=rel,
                    description="Custom React hook",
                    tags=self._infer_tags(f.stem),
                ))
        return assets

    def _detect_utils(self) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []
        util_dirs = ["utils", "lib", "helpers", "shared/utils"]
        for dir_name in util_dirs:
            for util_dir in safe_rglob(self.root, dir_name):
                if not util_dir.is_dir():
                    continue
                for f in util_dir.iterdir():
                    if f.suffix not in {".ts", ".js", ".py"} or f.stem == "index":
                        continue
                    assets.append(ReusableAsset(
                        name=f.stem,
                        asset_type="util",
                        path=str(f.relative_to(self.root)),
                        description="Utility module",
                        tags=self._infer_tags(f.stem),
                    ))
        return assets

    def _detect_services(self) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []
        for f in safe_rglob(self.root, "*service*"):
            if f.suffix not in {".ts", ".py"}:
                continue
            assets.append(ReusableAsset(
                name=f.stem,
                asset_type="service",
                path=str(f.relative_to(self.root)),
                description="Service layer module",
                tags=self._infer_tags(f.stem),
            ))
        return assets

    def _detect_python_assets(self) -> list[ReusableAsset]:
        assets: list[ReusableAsset] = []
        for f in safe_rglob(self.root, "*.py"):
            # decorators, base classes as shared utilities
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r"^class Base\w+", text, re.MULTILINE):
                assets.append(ReusableAsset(
                    name=f.stem,
                    asset_type="util",
                    path=str(f.relative_to(self.root)),
                    description="Python base class / shared utility",
                    tags=self._infer_tags(f.stem),
                ))
        return assets

    def _extract_ts_exports(self, f: Path) -> list[str]:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            return re.findall(r"export (?:default |const |function |class )(\w+)", text)
        except Exception:
            return []

    def _infer_tags(self, name: str) -> list[str]:
        _TAG_MAP = {
            "auth": ["auth"], "login": ["auth"], "otp": ["auth"],
            "payment": ["payment"], "pay": ["payment"],
            "user": ["user"], "profile": ["user"],
            "modal": ["ui", "modal"], "dialog": ["ui", "modal"],
            "form": ["ui", "form"], "input": ["ui", "form"],
            "table": ["ui", "table"], "list": ["ui"],
            "hook": ["hook"], "use": ["hook"],
            "util": ["util"], "helper": ["util"],
            "date": ["util", "date"], "format": ["util"],
            "api": ["api"], "client": ["api"],
            "notification": ["notification"], "toast": ["notification"],
            "chart": ["ui", "chart"], "graph": ["ui", "chart"],
        }
        name_lower = name.lower()
        tags: set[str] = set()
        for keyword, tag_list in _TAG_MAP.items():
            if keyword in name_lower:
                tags.update(tag_list)
        return sorted(tags)
