"""
Memory store — persists cognitive knowledge across sessions.

Layout (conflict-free, file-per-entry):

    <store_dir>/
      entries/<id>.json        # one memory entry per file
      syntheses/<domain>.json  # one synthesis per domain

Why file-per-entry: two devs adding decisions concurrently create different
files → zero git merge conflicts. Editing an existing entry touches only its
own file → conflict only if two devs edit the exact same entry, which is rare
and resolvable.

Legacy `memory.json` (single file with `entries` + `syntheses` dicts) is
auto-migrated on first init. The old file is renamed to `memory.json.migrated`
so nothing is lost.

Uses Qdrant for semantic search when available, falls back to substring search.
"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from precept.memory.schema import MemoryEntry, MemoryKind
from precept.storage import atomic_write_text, file_lock


def _entry_id(kind: str, domain: str, title: str) -> str:
    key = f"{kind}:{domain}:{title}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _safe_filename(s: str) -> str:
    """Make a string safe to use as a filename."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)


# ------------------------------------------------------------------
# Lightweight relevance scoring for the dependency-free file store.
# Not as good as the pgvector/Qdrant paths, but ranks far better than
# raw substring counting: weights title/tag hits, gives partial credit
# for stem overlap (idempot → idempotency), and adds a trigram fuzzy
# fallback so typos / morphology still surface the right entry.
# ------------------------------------------------------------------

_WORD_RE = re.compile(r"\w+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _trigrams(s: str) -> set[str]:
    s = f"  {s.lower().strip()}  "
    return {s[i : i + 3] for i in range(len(s) - 2)}


def _trigram_sim(a: str, b: str) -> float:
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _token_score(q_tokens: set[str], text_tokens: set[str], exact_w: float, partial_w: float) -> float:
    score = 0.0
    for qt in q_tokens:
        if qt in text_tokens:
            score += exact_w
        elif any(qt in tt or tt in qt for tt in text_tokens):
            score += partial_w
    return score


# ------------------------------------------------------------------
# Abstract base
# ------------------------------------------------------------------


class MemoryStore(ABC):
    @abstractmethod
    def save(self, entry: MemoryEntry) -> MemoryEntry: ...

    @abstractmethod
    def get(self, entry_id: str) -> MemoryEntry | None: ...

    @abstractmethod
    def search(self, query: str, kind: MemoryKind | None = None, domain: str = "", limit: int = 10) -> list[MemoryEntry]: ...

    @abstractmethod
    def list_by_domain(self, domain: str) -> list[MemoryEntry]: ...

    @abstractmethod
    def delete(self, entry_id: str) -> bool: ...

    @abstractmethod
    def all(self) -> list[MemoryEntry]: ...

    def mark_superseded(self, old_id: str, new_id: str) -> bool:
        """Mark `old_id` as replaced by `new_id`. Default no-op for stores
        that don't track supersession; override in concrete stores."""
        return False


# ------------------------------------------------------------------
# File-based store — directory of small files, conflict-free across devs
# ------------------------------------------------------------------


class FileMemoryStore(MemoryStore):
    """Memory store as a directory of per-entry JSON files."""

    def __init__(self, store_dir: str | Path) -> None:
        # Accept legacy `<ws>/memory.json` path and silently use its parent + 'memory'
        p = Path(store_dir)
        if p.suffix == ".json":
            p = p.parent / p.stem  # memory.json → memory
        self.dir = p
        self.entries_dir = self.dir / "entries"
        self.syntheses_dir = self.dir / "syntheses"
        self.entries_dir.mkdir(parents=True, exist_ok=True)
        self.syntheses_dir.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_json()

    # ------------------------------------------------------------------
    # Legacy migration — split old memory.json into per-entry files
    # ------------------------------------------------------------------

    def _migrate_legacy_json(self) -> None:
        """If `<parent>/memory.json` exists, split it into per-entry files once."""
        legacy = self.dir.parent / f"{self.dir.name}.json"
        if not legacy.exists():
            return
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        # Normalize: schema v2 has {entries, syntheses}; v1 was a flat {id: entry} dict.
        entries: dict = data.get("entries") if isinstance(data, dict) and "entries" in data else data
        syntheses: dict = data.get("syntheses", {}) if isinstance(data, dict) else {}

        if isinstance(entries, dict):
            for eid, raw in entries.items():
                if not isinstance(raw, dict):
                    continue
                self._write_entry_file(str(eid), raw)
        if isinstance(syntheses, dict):
            for domain, syn in syntheses.items():
                if isinstance(syn, dict):
                    self._write_synthesis_file(str(domain), syn)

        try:
            legacy.rename(legacy.with_suffix(legacy.suffix + ".migrated"))
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Disk I/O helpers
    # ------------------------------------------------------------------

    def _entry_file(self, entry_id: str) -> Path:
        return self.entries_dir / f"{_safe_filename(entry_id)}.json"

    def _synthesis_file(self, domain: str) -> Path:
        return self.syntheses_dir / f"{_safe_filename(domain)}.json"

    def _write_entry_file(self, entry_id: str, payload: dict) -> None:
        path = self._entry_file(entry_id)
        with file_lock(path):
            atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def _write_synthesis_file(self, domain: str, payload: dict) -> None:
        path = self._synthesis_file(domain)
        with file_lock(path):
            atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def _read_json(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def _iter_entry_files(self):
        if not self.entries_dir.exists():
            return
        yield from self.entries_dir.glob("*.json")

    def _load_all_entries(self, include_superseded: bool = False) -> list[dict]:
        out: list[dict] = []
        for p in self._iter_entry_files():
            raw = self._read_json(p)
            if raw is None:
                continue
            if not include_superseded and isinstance(raw.get("metadata"), dict) \
                    and raw["metadata"].get("superseded_by"):
                continue
            out.append(raw)
        return out

    def mark_superseded(self, old_id: str, new_id: str) -> bool:
        """Flag `old_id` as replaced by `new_id` via metadata.superseded_by.

        Superseded entries stay on disk for audit but are hidden from
        search / list / all (see `_load_all_entries`). Direct `get(id)`
        still returns them.
        """
        if not old_id or old_id == new_id:
            return False
        path = self._entry_file(old_id)
        raw = self._read_json(path)
        if raw is None:
            return False
        meta = raw.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}
        if meta.get("superseded_by"):
            return False
        from datetime import datetime, timezone
        meta["superseded_by"] = new_id
        meta["superseded_at"] = datetime.now(timezone.utc).isoformat()
        raw["metadata"] = meta
        self._write_entry_file(old_id, raw)
        return True

    # ------------------------------------------------------------------
    # Public API — entries
    # ------------------------------------------------------------------

    def save(self, entry: MemoryEntry) -> MemoryEntry:
        if not entry.id:
            entry.id = _entry_id(entry.kind.value, entry.domain, entry.title)
        payload = entry.model_dump(mode="json")
        self._write_entry_file(entry.id, payload)
        # mark this domain's synthesis stale (new evidence arrived)
        syn_path = self._synthesis_file(entry.domain)
        syn = self._read_json(syn_path)
        if syn is not None:
            syn["stale"] = True
            self._write_synthesis_file(entry.domain, syn)
        return entry

    def get(self, entry_id: str) -> MemoryEntry | None:
        raw = self._read_json(self._entry_file(entry_id))
        return MemoryEntry(**raw) if raw else None

    def search(self, query: str, kind: MemoryKind | None = None, domain: str = "", limit: int = 10) -> list[MemoryEntry]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        results: list[tuple[float, MemoryEntry]] = []
        for raw in self._load_all_entries():
            e = MemoryEntry(**raw)
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
        return [MemoryEntry(**r) for r in self._load_all_entries() if r.get("domain") == domain]

    def delete(self, entry_id: str) -> bool:
        path = self._entry_file(entry_id)
        if not path.exists():
            return False
        try:
            path.unlink()
            return True
        except OSError:
            return False

    def all(self) -> list[MemoryEntry]:
        return [MemoryEntry(**r) for r in self._load_all_entries()]

    # ------------------------------------------------------------------
    # Synthesis API — one file per domain (`syntheses/<domain>.json`)
    # ------------------------------------------------------------------

    def get_synthesis(self, domain: str) -> dict | None:
        return self._read_json(self._synthesis_file(domain))

    def save_synthesis(
        self,
        domain: str,
        summary: str,
        key_themes: list[str],
        open_questions: list[str],
        synthesized_by: str = "ai",
    ) -> dict:
        from datetime import datetime, timezone

        entry_ids = [
            r.get("id", "")
            for r in self._load_all_entries()
            if r.get("domain") == domain
        ]
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
        self._write_synthesis_file(domain, synthesis)
        return synthesis

    def synthesis_stale(self, domain: str) -> bool:
        syn = self.get_synthesis(domain)
        if not syn:
            return True
        if syn.get("stale"):
            return True
        current_count = sum(
            1 for r in self._load_all_entries() if r.get("domain") == domain
        )
        return current_count != syn.get("entry_count_at_synthesis", 0)


# ------------------------------------------------------------------
# Qdrant-backed store (optional, semantic search)
# ------------------------------------------------------------------


class QdrantMemoryStore(MemoryStore):
    """Vector-based memory using Qdrant. Falls back to FileMemoryStore when unavailable."""

    COLLECTION = "precept_memory"
    VECTOR_SIZE = 384

    def __init__(self, url: str = "http://localhost:6333", api_key: str = "", fallback_dir: str = ".precept/memory") -> None:
        self._fallback = FileMemoryStore(fallback_dir)
        self._client = None
        self._encoder = None
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            client = QdrantClient(url=url, api_key=api_key or None, timeout=3)
            client.get_collections()
            existing = [c.name for c in client.get_collections().collections]
            if self.COLLECTION not in existing:
                client.create_collection(
                    collection_name=self.COLLECTION,
                    vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE),
                )
            self._client = client
            self._encoder = self._load_encoder()
        except Exception:
            pass

    def _load_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            return None

    def _encode(self, text: str) -> list[float] | None:
        if self._encoder:
            return self._encoder.encode(text).tolist()
        return None

    def _available(self) -> bool:
        return self._client is not None

    def save(self, entry: MemoryEntry) -> MemoryEntry:
        self._fallback.save(entry)
        if not self._available():
            return entry
        try:
            from qdrant_client.models import PointStruct
            text = f"{entry.title} {entry.body}"
            vec = self._encode(text)
            if vec:
                self._client.upsert(
                    collection_name=self.COLLECTION,
                    points=[PointStruct(
                        id=abs(hash(entry.id)) % (2**31),
                        vector=vec,
                        payload=entry.model_dump(mode="json"),
                    )],
                )
        except Exception:
            pass
        return entry

    def search(self, query: str, kind: MemoryKind | None = None, domain: str = "", limit: int = 10) -> list[MemoryEntry]:
        if not self._available() or not self._encoder:
            return self._fallback.search(query, kind, domain, limit)
        try:
            from qdrant_client.models import FieldCondition, Filter, MatchValue
            vec = self._encode(query)
            filters = []
            if kind:
                filters.append(FieldCondition(key="kind", match=MatchValue(value=kind.value)))
            if domain:
                filters.append(FieldCondition(key="domain", match=MatchValue(value=domain)))
            results = self._client.search(
                collection_name=self.COLLECTION,
                query_vector=vec,
                limit=limit,
                query_filter=Filter(must=filters) if filters else None,
            )
            return [MemoryEntry(**r.payload) for r in results]
        except Exception:
            return self._fallback.search(query, kind, domain, limit)

    def get(self, entry_id: str) -> MemoryEntry | None:
        return self._fallback.get(entry_id)

    def list_by_domain(self, domain: str) -> list[MemoryEntry]:
        return self._fallback.list_by_domain(domain)

    def delete(self, entry_id: str) -> bool:
        return self._fallback.delete(entry_id)

    def all(self) -> list[MemoryEntry]:
        return self._fallback.all()

    def mark_superseded(self, old_id: str, new_id: str) -> bool:
        return self._fallback.mark_superseded(old_id, new_id)

    def get_synthesis(self, domain: str) -> dict | None:
        return self._fallback.get_synthesis(domain)

    def save_synthesis(self, domain: str, summary: str, key_themes: list[str],
                       open_questions: list[str], synthesized_by: str = "ai") -> dict:
        return self._fallback.save_synthesis(domain, summary, key_themes, open_questions, synthesized_by)

    def synthesis_stale(self, domain: str) -> bool:
        return self._fallback.synthesis_stale(domain)


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------


def create_store(repo_path: str = ".", qdrant_url: str = "", qdrant_api_key: str = "") -> MemoryStore:
    """
    Return the best available store for the given repo.

    Resolution order:
    1. POSTGRES_USER env set → PostgresMemoryStore (DSN built from POSTGRES_* vars).
       Schema auto-bootstraps on first connect (zero setting).
    2. Workspace config present → central FileMemoryStore at <workspace>/memory/.
    3. Legacy per-repo .precept/memory/.
    """
    import os

    from precept.link.resolver import resolve_workspace_or_legacy

    if os.getenv("POSTGRES_USER"):
        try:
            from precept.memory.postgres_store import PostgresMemoryStore
            return PostgresMemoryStore()
        except ImportError:
            # psycopg not installed — fall through to file store
            pass

    memory_path, _, _mode = resolve_workspace_or_legacy(repo_path)
    if qdrant_url:
        return QdrantMemoryStore(url=qdrant_url, api_key=qdrant_api_key, fallback_dir=str(memory_path))
    return FileMemoryStore(store_dir=str(memory_path))
