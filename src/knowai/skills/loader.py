"""
Skills loader — reads user-authored knowledge from workspace/skills/*.md.

Each skill is a Markdown file with simple YAML-style frontmatter:

    ---
    name: ui-style
    description: Use when working on UI components (Tailwind v4, design tokens, buttons).
    tags: [ui, frontend]
    ---

    # UI Style Guide

    - Use Tailwind v4 utility classes
    - Money: format as "THB X,XXX.XX"
    - All buttons must use <Button> from src/components/ui/Button.tsx

The name + description are surfaced to Claude via the `list_skills` MCP tool,
so Claude can decide which skill is relevant to the task and call `read_skill`
to pull the full body when needed.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from knowai.paths import workspace_skills_dir


class Skill(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    body: str = ""
    source_path: str = ""


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """
    Split a markdown file into (frontmatter_dict, body).

    Frontmatter is delimited by `---` on its own line, both at the start of
    the file and again to close the block. Only flat `key: value` and
    `key: [a, b, c]` lines are supported — enough for skill metadata.
    Anything fancier should go in the body.
    """
    if not text.startswith("---"):
        return {}, text
    rest = text[3:].lstrip("\r\n")
    end = rest.find("\n---")
    if end < 0:
        return {}, text
    fm_block = rest[:end]
    body = rest[end + 4 :].lstrip("\r\n")

    data: dict[str, object] = {}
    for raw_line in fm_block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            items = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
            data[k] = items
        else:
            data[k] = v.strip('"').strip("'")
    return data, body


def _skill_from_file(path: Path) -> Skill | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    data, body = _parse_frontmatter(text)
    name = str(data.get("name") or path.stem)
    description = str(data.get("description") or "")
    raw_tags = data.get("tags") or []
    tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else []
    return Skill(
        name=name,
        description=description,
        tags=tags,
        body=body.strip(),
        source_path=str(path),
    )


def load_workspace_skills(workspace_name: str) -> list[Skill]:
    """
    Return every skill visible to AI for this workspace.

    Merge order:
    1. Built-in skills (auth, billing/payment, otp, webhook, order, etc.)
       — ship with knowai as sensible defaults derived from cognition packs.
    2. Workspace skills (`<workspace>/skills/*.md`) — team-authored.

    Workspace skills override built-ins of the same `name`. So a team can
    customize the default `billing` skill by writing `skills/billing.md`
    in their workspace.
    """
    by_name: dict[str, Skill] = {s.name: s for s in load_builtin_skills()}

    skills_dir = workspace_skills_dir(workspace_name)
    if skills_dir.exists():
        for path in sorted(skills_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            s = _skill_from_file(path)
            if s is not None:
                by_name[s.name] = s  # workspace overrides builtin

    return sorted(by_name.values(), key=lambda s: s.name)


def load_builtin_skills() -> list[Skill]:
    """
    Skills shipped with knowai — derived from BUILTIN_PACKS at runtime
    so we have one source of truth for default domain knowledge.

    Users can override any of these by writing `skills/<same-name>.md` in
    their workspace.
    """
    try:
        from knowai.packs.builtin import BUILTIN_PACKS
    except Exception:
        return []
    return [_skill_from_pack(domain, pack) for domain, pack in BUILTIN_PACKS.items()]


def _skill_from_pack(domain: str, pack) -> Skill:
    """Render a CognitionPack as a markdown-style Skill (built-in default)."""
    body_lines: list[str] = [f"# {domain.capitalize()} — built-in guidance", ""]
    if pack.description:
        body_lines.extend([pack.description, ""])

    def section(title: str, items: list[str]) -> None:
        if not items:
            return
        body_lines.append(f"## {title}")
        body_lines.extend(f"- {item}" for item in items)
        body_lines.append("")

    section("Business rules", pack.business_rules)
    section("Common requirements", pack.common_requirements)
    section("Risk flags", pack.risk_flags)
    section("Required workflow", pack.required_workflow)
    section("Forbidden shortcuts", pack.forbidden_shortcuts)
    section("Questions to ask", pack.questions_to_ask)
    if pack.related_domains:
        section("Related domains", pack.related_domains)

    return Skill(
        name=domain,
        description=f"Built-in: {pack.description or domain + ' domain guidance'}",
        tags=[domain, "builtin", *pack.related_domains],
        body="\n".join(body_lines).strip(),
        source_path=f"<builtin:{domain}>",
    )


def read_skill(workspace_name: str, name: str) -> Skill | None:
    """Read a single skill by its `name` (matches frontmatter name or filename stem)."""
    for s in load_workspace_skills(workspace_name):
        if s.name == name or Path(s.source_path).stem == name:
            return s
    return None
