"""
Memory store — persists cognitive knowledge across sessions.

Uses JSON file by default (zero dependencies).
Upgrades to Qdrant vector search automatically when qdrant-client is installed
and QDRANT_URL is reachable.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from knowlyx.memory.schema import MemoryEntry, MemoryKind


def _entry_id(kind: str, domain: str, title: str) -> str:
    key = f"{kind}:{domain}:{title}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


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


# ------------------------------------------------------------------
# File-based store (default, zero deps)
# ------------------------------------------------------------------


class FileMemoryStore(MemoryStore):
    """Stores memory as JSON. Works everywhere, no server needed."""

    def __init__(self, store_path: str | Path = ".knowlyx/memory.json") -> None:
        self.path = Path(store_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def _flush(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")

    def save(self, entry: MemoryEntry) -> MemoryEntry:
        if not entry.id:
            entry.id = _entry_id(entry.kind.value, entry.domain, entry.title)
        self._data[entry.id] = entry.model_dump(mode="json")
        self._flush()
        return entry

    def get(self, entry_id: str) -> MemoryEntry | None:
        raw = self._data.get(entry_id)
        return MemoryEntry(**raw) if raw else None

    def search(self, query: str, kind: MemoryKind | None = None, domain: str = "", limit: int = 10) -> list[MemoryEntry]:
        q = query.lower()
        results: list[tuple[int, MemoryEntry]] = []
        for raw in self._data.values():
            e = MemoryEntry(**raw)
            if kind and e.kind != kind:
                continue
            if domain and e.domain != domain:
                continue
            # simple keyword relevance score
            text = f"{e.title} {e.body} {' '.join(e.tags)}".lower()
            score = sum(1 for word in q.split() if word in text)
            if score:
                results.append((score, e))
        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:limit]]

    def list_by_domain(self, domain: str) -> list[MemoryEntry]:
        return [MemoryEntry(**r) for r in self._data.values() if r.get("domain") == domain]

    def delete(self, entry_id: str) -> bool:
        if entry_id in self._data:
            del self._data[entry_id]
            self._flush()
            return True
        return False

    def all(self) -> list[MemoryEntry]:
        return [MemoryEntry(**r) for r in self._data.values()]


# ------------------------------------------------------------------
# Qdrant-backed store (optional, semantic search)
# ------------------------------------------------------------------


class QdrantMemoryStore(MemoryStore):
    """
    Vector-based memory using Qdrant.
    Falls back to FileMemoryStore if qdrant-client not installed or unreachable.
    """

    COLLECTION = "knowlyx_memory"
    VECTOR_SIZE = 384  # all-MiniLM-L6-v2 dimension

    def __init__(self, url: str = "http://localhost:6333", api_key: str = "", fallback_path: str = ".knowlyx/memory.json") -> None:
        self._fallback = FileMemoryStore(fallback_path)
        self._client = None
        self._encoder = None
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            client = QdrantClient(url=url, api_key=api_key or None, timeout=3)
            client.get_collections()  # connectivity check
            # ensure collection exists
            existing = [c.name for c in client.get_collections().collections]
            if self.COLLECTION not in existing:
                client.create_collection(
                    collection_name=self.COLLECTION,
                    vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE),
                )
            self._client = client
            self._encoder = self._load_encoder()
        except Exception:
            pass  # graceful fallback

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
        self._fallback.save(entry)  # always persist to file too
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
            from qdrant_client.models import Filter, FieldCondition, MatchValue
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


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------


def create_store(repo_path: str = ".", qdrant_url: str = "", qdrant_api_key: str = "") -> MemoryStore:
    """
    Return the best available store for the given repo.

    Resolution order:
    1. If repo has .knowlyx/config.toml (or any ancestor does), use the
       central workspace store at ~/.knowlyx/workspaces/<name>/memory.json
       — shared across all repos in the same workspace.
    2. Otherwise fall back to legacy per-repo .knowlyx/memory.json.
    """
    from knowlyx.link.resolver import resolve_workspace_or_legacy

    memory_path, _, _mode = resolve_workspace_or_legacy(repo_path)
    if qdrant_url:
        return QdrantMemoryStore(url=qdrant_url, api_key=qdrant_api_key, fallback_path=str(memory_path))
    return FileMemoryStore(store_path=str(memory_path))
