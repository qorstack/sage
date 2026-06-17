"""
OKF (Open Knowledge Format) memory store — knowledge as editable Markdown.

Each entry is a Markdown file with a small YAML frontmatter block, laid out by
domain so humans and AI agents can read/edit/diff it directly in the repo:

    agents/preceptai/
      index.md
      <domain>/
        index.md
        rules.md                       # editable cognition rules (precept.rules)
        decisions/<slug>.md            # team decisions / business context
        skills/<slug>.md               # skills
        notes/<slug>.md                # everything else
        synthesis.md                   # per-domain synthesis

This is the source of truth (git-syncable, conflict-light). A vector index
(SqliteMemoryStore) can wrap it for semantic search; the index is derived and
never the source of truth.

Mirrors FileMemoryStore semantics exactly: id via `_entry_id`, supersession via
`metadata.superseded_by` (hidden from all/search/list, still returned by get),
and the same synthesis dict shape.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from precept.memory.schema import MemoryEntry, MemoryKind, MemoryScope, MemorySource
from precept.memory.store import (
    MemoryStore,
    _entry_id,
    _token_score,
    _tokenize,
    _trigram_sim,
)
from precept.storage import atomic_write_text

_RESERVED = {"index.md", "rules.md", "synthesis.md"}
_DECISION_KINDS = {"team_decision", "business_context"}


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "entry"


def _kind_folder(kind_value: str) -> str:
    if kind_value in _DECISION_KINDS:
        return "decisions"
    if "skill" in kind_value:
        return "skills"
    return "notes"


# ------------------------------------------------------------------
# Minimal YAML frontmatter codec (flat: str / list[str] / bool)
# ------------------------------------------------------------------

def _fm_scalar(value: str) -> str:
    # Quote to survive colons / leading specials; escape embedded quotes.
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _serialize(entry: MemoryEntry) -> str:
    meta = dict(entry.metadata or {})
    superseded_by = meta.pop("superseded_by", "")
    superseded_at = meta.pop("superseded_at", "")
    fm = [
        "---",
        f"id: {_fm_scalar(entry.id)}",
        f"type: {_fm_scalar(entry.kind.value)}",
        f"title: {_fm_scalar(entry.title)}",
        f"domain: {_fm_scalar(entry.domain)}",
        "tags: [" + ", ".join(_fm_scalar(t) for t in entry.tags) + "]",
        f"scope: {_fm_scalar(entry.scope.value)}",
        f"workspace: {_fm_scalar(entry.workspace)}",
        f"repo_name: {_fm_scalar(entry.repo_name)}",
        f"source: {_fm_scalar(entry.source.value)}",
        f"approved: {'true' if entry.approved else 'false'}",
        f"approved_by: {_fm_scalar(entry.approved_by)}",
        f"enforcement: {_fm_scalar(entry.enforcement)}",
        f"timestamp: {_fm_scalar(entry.created_at.isoformat())}",
    ]
    if entry.applies_to:
        fm.append("applies_to: [" + ", ".join(_fm_scalar(a) for a in entry.applies_to) + "]")
    if entry.supersedes:
        fm.append(f"supersedes: {_fm_scalar(entry.supersedes)}")
    if entry.related:
        fm.append("related: [" + ", ".join(_fm_scalar(r) for r in entry.related) + "]")
    if superseded_by:
        fm.append(f"superseded_by: {_fm_scalar(str(superseded_by))}")
        fm.append(f"superseded_at: {_fm_scalar(str(superseded_at))}")
    if meta:
        fm.append(f"metadata: {_fm_scalar(json.dumps(meta, ensure_ascii=False))}")
    fm.append("---")
    fm.append("")
    return "\n".join(fm) + "\n" + (entry.body or "") + "\n"


def _parse_value(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_unquote(part.strip()) for part in _split_list(inner)]
    if raw in ("true", "false"):
        return raw == "true"
    return _unquote(raw)


def _split_list(inner: str) -> list[str]:
    # Split on commas that aren't inside quotes.
    out, buf, in_q = [], [], False
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == '"' and (not buf or buf[-1] != "\\"):
            in_q = not in_q
            buf.append(c)
        elif c == "," and not in_q:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    if buf:
        out.append("".join(buf))
    return out


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return s


def _deserialize(text: str) -> MemoryEntry | None:
    if not text.startswith("---"):
        return None
    parts = text.split("\n")
    if parts[0].strip() != "---":
        return None
    fm: dict = {}
    i = 1
    while i < len(parts) and parts[i].strip() != "---":
        line = parts[i]
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = _parse_value(val)
        i += 1
    body = "\n".join(parts[i + 1:]).strip("\n") if i < len(parts) else ""
    if not fm.get("id"):
        return None
    meta: dict = {}
    raw_meta = fm.get("metadata")
    if isinstance(raw_meta, str) and raw_meta:
        try:
            meta = json.loads(raw_meta)
        except Exception:
            meta = {}
    if fm.get("superseded_by"):
        meta["superseded_by"] = fm["superseded_by"]
        if fm.get("superseded_at"):
            meta["superseded_at"] = fm["superseded_at"]
    try:
        return MemoryEntry(
            id=str(fm["id"]),
            kind=MemoryKind(fm.get("type", "team_decision")),
            domain=str(fm.get("domain", "")),
            title=str(fm.get("title", "")),
            body=body,
            tags=list(fm.get("tags", []) or []),
            approved=bool(fm.get("approved", False)),
            approved_by=str(fm.get("approved_by", "")),
            scope=MemoryScope(fm.get("scope", "global")),
            source=MemorySource(fm.get("source", "human")),
            workspace=str(fm.get("workspace", "")),
            repo_name=str(fm.get("repo_name", "")),
            enforcement=str(fm.get("enforcement", "advise")),
            applies_to=list(fm.get("applies_to", []) or []),
            supersedes=str(fm.get("supersedes", "")),
            related=list(fm.get("related", []) or []),
            created_at=_parse_dt(fm.get("timestamp", "")),
            metadata=meta,
        )
    except Exception:
        return None


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


class OkfMemoryStore(MemoryStore):
    """Knowledge as OKF Markdown under `agents/preceptai/`, organized by domain."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self._ensure_root_index()

    # ---- layout helpers ----------------------------------------------------

    def _ensure_root_index(self) -> None:
        idx = self.root / "index.md"
        if not idx.exists():
            atomic_write_text(idx, _ROOT_INDEX)

    def _ensure_domain_index(self, domain: str) -> None:
        d = self.root / domain
        d.mkdir(parents=True, exist_ok=True)
        idx = d / "index.md"
        if not idx.exists():
            atomic_write_text(idx, f"# {domain}\n\nTeam knowledge for the **{domain}** domain.\n")

    def _iter_entry_files(self):
        for p in self.root.rglob("*.md"):
            if p.name not in _RESERVED:
                yield p

    def _find_path_by_id(self, entry_id: str) -> Path | None:
        for p in self._iter_entry_files():
            try:
                head = p.read_text(encoding="utf-8")[:600]
            except OSError:
                continue
            if f'id: "{entry_id}"' in head or f"id: {entry_id}" in head:
                # confirm via full parse (id may collide on substring)
                e = _deserialize(p.read_text(encoding="utf-8"))
                if e and e.id == entry_id:
                    return p
        return None

    def _entry_path(self, entry: MemoryEntry) -> Path:
        existing = self._find_path_by_id(entry.id)
        if existing:
            return existing
        folder = self.root / entry.domain / _kind_folder(entry.kind.value)
        folder.mkdir(parents=True, exist_ok=True)
        base = _slug(entry.title)
        path = folder / f"{base}.md"
        if path.exists():  # slug collision with a different id
            path = folder / f"{base}-{entry.id[:6]}.md"
        return path

    def _load_all(self, include_superseded: bool = False) -> list[MemoryEntry]:
        out: list[MemoryEntry] = []
        for p in self._iter_entry_files():
            try:
                e = _deserialize(p.read_text(encoding="utf-8"))
            except OSError:
                e = None
            if e is None:
                continue
            if not include_superseded and (e.metadata or {}).get("superseded_by"):
                continue
            out.append(e)
        return out

    # ---- MemoryStore API ---------------------------------------------------

    def save(self, entry: MemoryEntry) -> MemoryEntry:
        if not entry.id:
            entry.id = _entry_id(entry.kind.value, entry.domain, entry.title)
        self._ensure_domain_index(entry.domain)
        atomic_write_text(self._entry_path(entry), _serialize(entry))
        # mark this domain's synthesis stale (new evidence)
        syn = self.get_synthesis(entry.domain)
        if syn is not None:
            syn["stale"] = True
            atomic_write_text(self._synthesis_path(entry.domain), _synthesis_to_md(entry.domain, syn))
        return entry

    def get(self, entry_id: str) -> MemoryEntry | None:
        p = self._find_path_by_id(entry_id)
        return _deserialize(p.read_text(encoding="utf-8")) if p else None

    def search(self, query: str, kind: MemoryKind | None = None, domain: str = "", limit: int = 10) -> list[MemoryEntry]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        results: list[tuple[float, MemoryEntry]] = []
        for e in self._load_all():
            if kind and e.kind != kind:
                continue
            if domain and e.domain != domain:
                continue
            score = (
                _token_score(q_tokens, _tokenize(e.title), exact_w=3.0, partial_w=1.5)
                + _token_score(q_tokens, _tokenize(" ".join(e.tags)), exact_w=2.0, partial_w=0.8)
                + _token_score(q_tokens, _tokenize(e.body), exact_w=1.0, partial_w=0.4)
                + 1.5 * _trigram_sim(query, e.title)
            )
            if score > 0:
                results.append((score, e))
        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:limit]]

    def list_by_domain(self, domain: str) -> list[MemoryEntry]:
        return [e for e in self._load_all() if e.domain == domain]

    def delete(self, entry_id: str) -> bool:
        p = self._find_path_by_id(entry_id)
        if not p:
            return False
        try:
            p.unlink()
            return True
        except OSError:
            return False

    def all(self) -> list[MemoryEntry]:
        return self._load_all()

    def mark_superseded(self, old_id: str, new_id: str) -> bool:
        if not old_id or old_id == new_id:
            return False
        e = self.get(old_id)
        if e is None or (e.metadata or {}).get("superseded_by"):
            return False
        meta = dict(e.metadata or {})
        meta["superseded_by"] = new_id
        meta["superseded_at"] = datetime.now(timezone.utc).isoformat()
        e.metadata = meta
        atomic_write_text(self._entry_path(e), _serialize(e))
        return True

    # ---- synthesis ---------------------------------------------------------

    def _synthesis_path(self, domain: str) -> Path:
        return self.root / domain / "synthesis.md"

    def get_synthesis(self, domain: str) -> dict | None:
        p = self._synthesis_path(domain)
        if not p.exists():
            return None
        return _synthesis_from_md(p.read_text(encoding="utf-8"))

    def save_synthesis(self, domain: str, summary: str, key_themes: list[str],
                       open_questions: list[str], synthesized_by: str = "ai") -> dict:
        entry_ids = [e.id for e in self._load_all() if e.domain == domain]
        synthesis = {
            "summary": summary,
            "key_themes": key_themes,
            "open_questions": open_questions,
            "synthesized_at": datetime.now(timezone.utc).isoformat(),
            "synthesized_by": synthesized_by,
            "entry_count_at_synthesis": len(entry_ids),
            "entry_ids": entry_ids,
            "stale": False,
        }
        self._ensure_domain_index(domain)
        atomic_write_text(self._synthesis_path(domain), _synthesis_to_md(domain, synthesis))
        return synthesis

    def synthesis_stale(self, domain: str) -> bool:
        syn = self.get_synthesis(domain)
        return bool(syn and syn.get("stale"))


_ROOT_INDEX = """# Precept knowledge (OKF)

Open Knowledge Format: each file is Markdown with a small YAML frontmatter
header, organized by domain. Humans and AI agents read and edit these directly;
commit them so the team shares the same context.

- `<domain>/rules.md` — editable cognition rules
- `<domain>/decisions/` — team decisions
- `<domain>/skills/` — skills
- `<domain>/synthesis.md` — distilled per-domain summary
"""


def _synthesis_to_md(domain: str, syn: dict) -> str:
    fm = [
        "---",
        'type: "synthesis"',
        f'domain: {_fm_scalar(domain)}',
        f"stale: {'true' if syn.get('stale') else 'false'}",
        f'synthesized_at: {_fm_scalar(str(syn.get("synthesized_at", "")))}',
        f'synthesized_by: {_fm_scalar(str(syn.get("synthesized_by", "ai")))}',
        f"entry_count_at_synthesis: {int(syn.get('entry_count_at_synthesis', 0))}",
        "entry_ids: [" + ", ".join(_fm_scalar(i) for i in syn.get("entry_ids", [])) + "]",
        "key_themes: [" + ", ".join(_fm_scalar(t) for t in syn.get("key_themes", [])) + "]",
        "open_questions: [" + ", ".join(_fm_scalar(q) for q in syn.get("open_questions", [])) + "]",
        "---",
        "",
    ]
    return "\n".join(fm) + "\n" + (syn.get("summary", "") or "") + "\n"


def _synthesis_from_md(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("\n")
    fm: dict = {}
    i = 1
    while i < len(parts) and parts[i].strip() != "---":
        line = parts[i]
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = _parse_value(v)
        i += 1
    summary = "\n".join(parts[i + 1:]).strip("\n") if i < len(parts) else ""
    return {
        "summary": summary,
        "key_themes": list(fm.get("key_themes", []) or []),
        "open_questions": list(fm.get("open_questions", []) or []),
        "synthesized_at": fm.get("synthesized_at", ""),
        "synthesized_by": fm.get("synthesized_by", "ai"),
        "entry_count_at_synthesis": int(fm.get("entry_count_at_synthesis", 0) or 0),
        "entry_ids": list(fm.get("entry_ids", []) or []),
        "stale": bool(fm.get("stale", False)),
    }


def migrate_to_okf(repo_path: str | Path, root: str | Path) -> int:
    """Best-effort: copy legacy `.precept/` JSON entries into the OKF tree.

    Runs only when the OKF tree has no entries yet and a legacy store exists.
    Returns the number of entries migrated.
    """
    from precept.memory.store import FileMemoryStore

    okf = OkfMemoryStore(root)
    if okf._load_all(include_superseded=True):
        return 0  # already populated
    legacy_dir = Path(repo_path) / ".precept" / "memory"
    if not (legacy_dir / "entries").exists():
        legacy_dir = Path(repo_path) / ".precept"
    if not (legacy_dir / "entries").exists():
        return 0
    legacy = FileMemoryStore(legacy_dir)
    count = 0
    for entry in legacy.all():
        okf.save(entry)
        count += 1
    return count
