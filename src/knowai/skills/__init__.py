"""User-authored skills — Markdown knowledge files in workspace/skills/.

Built-in default skills (auth, payment, webhook, order, etc.) are merged in
automatically so even a fresh workspace gets sensible domain guidance. Teams
override any built-in by creating `skills/<same-name>.md` with their own.
"""

from knowai.skills.loader import (
    Skill,
    load_builtin_skills,
    load_workspace_skills,
    read_skill,
)

__all__ = ["Skill", "load_builtin_skills", "load_workspace_skills", "read_skill"]
