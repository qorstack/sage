"""
Postgres-backed memory store with auto-bootstrap (zero setting).

Activated when KNOWAI_DB_URL (or legacy KNOWLYX_DB_URL) is set, or when the
default docker-compose Postgres is reachable on localhost:5432.

Bootstrap is idempotent: schema.sql runs on every connect; CREATE ... IF NOT
EXISTS / DO $$ guards make repeats free. Team workflow:

    1. cp .env.example .env
    2. docker compose up -d
    3. knowai init                # writes .knowai/config.toml + MCP config

After that, just code + chat. The store auto-supersedes stale entries via
cosine similarity, and the synthesis-stale flag fires from a DB trigger so
every write path is covered.
"""

from __future__ import annotations

import json
import os
from importlib import resources
from typing import Any

from knowlyx.memory.schema import MemoryEntry, MemoryKind
from knowlyx.memory.store import MemoryStore

DEFAULT_DSN = "postgresql://knowai:knowai@localhost:5432/knowai"  # noqa: S105 - local docker-compose default
DEFAULT_SCHEMA = "public"
SIMILARITY_THRESHOLD = float(os.getenv("KNOWAI_SIMILARITY_THRESHOLD", "0.92"))


def _validate_schema_name(name: str) -> str:
    """Allow only safe identifier chars — schema name is interpolated into DDL."""
    if not name or not all(c.isalnum() or c == "_" for c in name):
        raise ValueError(f"Invalid schema name: {name!r}")
    return name


def _load_schema_sql() -> str:
    return resources.files("knowlyx.memory.sql").joinpath("schema.sql").read_text(encoding="utf-8")


class PostgresMemoryStore(MemoryStore):
    """Postgres + pgvector store. Bootstraps schema on first connect."""

    def __init__(self, dsn: str = "", schema: str = "") -> None:
        import psycopg
        from psycopg_pool import ConnectionPool

        self._dsn = (
            dsn
            or os.getenv("KNOWAI_DB_URL")
            or os.getenv("KNOWLYX_DB_URL")
            or DEFAULT_DSN
        )
        self._schema = _validate_schema_name(
            schema or os.getenv("KNOWAI_DB_SCHEMA") or DEFAULT_SCHEMA
        )

        def _configure(conn):
            # Run on every new pool connection so every query sees the right schema.
            # public stays in search_path so pgvector/pg_trgm types resolve.
            conn.execute(f'SET search_path TO "{self._schema}", public')

        self._pool = ConnectionPool(
            self._dsn,
            min_size=1,
            max_size=4,
            kwargs={"autocommit": True},
            configure=_configure,
        )
        self._psycopg = psycopg
        self._encoder = self._load_encoder()
        self._bootstrap()

    def _load_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            return None

    def _encode(self, text: str) -> list[float] | None:
        if self._encoder is None:
            return None
        return self._encoder.encode(text).tolist()

    def _bootstrap(self) -> None:
        sql = _load_schema_sql()
        with self._pool.connection() as conn:
            # Extensions must live in a shared schema (public) so the vector
            # type resolves regardless of which schema knowai's tables are in.
            conn.execute('CREATE EXTENSION IF NOT EXISTS vector  WITH SCHEMA public')
            conn.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public')
            conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{self._schema}"')
            # _configure already set search_path on this connection, so unqualified
            # CREATE TABLE / FUNCTION statements in schema.sql land in self._schema.
            conn.execute(sql)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_entry(row: dict) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            kind=MemoryKind(row["kind"]),
            domain=row["domain"],
            title=row["title"],
            body=row["body"],
            tags=list(row.get("tags") or []),
            approved=row.get("approved", False),
            approved_by=row.get("approved_by") or "",
            repo_path=row.get("repo_path") or "",
            created_at=row["created_at"],
            metadata=row.get("metadata") or {},
        )

    # ------------------------------------------------------------------
    # MemoryStore implementation
    # ------------------------------------------------------------------

    def save(self, entry: MemoryEntry) -> MemoryEntry:
        if not entry.id:
            import hashlib
            key = f"{entry.kind.value}:{entry.domain}:{entry.title}"
            entry.id = hashlib.sha256(key.encode()).hexdigest()[:16]

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memory_entries
                        (id, kind, domain, title, body, tags, approved, approved_by, repo_path, metadata)
                    VALUES (%s, %s::memory_kind, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        title       = EXCLUDED.title,
                        body        = EXCLUDED.body,
                        tags        = EXCLUDED.tags,
                        approved    = EXCLUDED.approved,
                        approved_by = EXCLUDED.approved_by,
                        repo_path   = EXCLUDED.repo_path,
                        metadata    = EXCLUDED.metadata
                    """,
                    (
                        entry.id, entry.kind.value, entry.domain, entry.title, entry.body,
                        entry.tags, entry.approved, entry.approved_by, entry.repo_path,
                        json.dumps(entry.metadata, default=str),
                    ),
                )
                cur.execute(
                    "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, 'insert', %s, %s::jsonb)",
                    (entry.id, entry.approved_by or "system", json.dumps({"title": entry.title})),
                )

            vec = self._encode(f"{entry.title} {entry.body}")
            if vec is not None:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO memory_entry_embeddings (entry_id, embedding)
                        VALUES (%s, %s::vector)
                        ON CONFLICT (entry_id) DO UPDATE SET
                            embedding  = EXCLUDED.embedding,
                            updated_at = now()
                        """,
                        (entry.id, vec),
                    )
                self._auto_supersede(conn, entry, vec)

        return entry

    def _auto_supersede(self, conn, entry: MemoryEntry, vec: list[float]) -> None:
        """Mark older entries in the same domain as superseded if very similar."""
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.id
                FROM memory_entries e
                JOIN memory_entry_embeddings em ON em.entry_id = e.id
                WHERE e.domain = %s
                  AND e.id <> %s
                  AND e.superseded_by IS NULL
                  AND (1 - (em.embedding <=> %s::vector)) >= %s
                """,
                (entry.domain, entry.id, vec, SIMILARITY_THRESHOLD),
            )
            stale_ids = [r[0] for r in cur.fetchall()]
            for sid in stale_ids:
                cur.execute(
                    "UPDATE memory_entries SET superseded_by = %s, superseded_at = now() WHERE id = %s",
                    (entry.id, sid),
                )
                cur.execute(
                    "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, 'supersede', 'auto', %s::jsonb)",
                    (sid, json.dumps({"superseded_by": entry.id})),
                )

    def get(self, entry_id: str) -> MemoryEntry | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT * FROM memory_entries WHERE id = %s", (entry_id,)
            ).fetchone()
        return self._row_to_entry(self._as_dict(conn, row)) if row else None

    def _as_dict(self, conn, row) -> dict:
        cols = [d[0] for d in conn.cursor().description] if row else []
        return dict(zip(cols, row)) if row else {}

    def search(self, query: str, kind: MemoryKind | None = None, domain: str = "", limit: int = 10) -> list[MemoryEntry]:
        vec = self._encode(query)
        with self._pool.connection() as conn:
            if vec is not None:
                sql = """
                    SELECT e.*, (1 - (em.embedding <=> %s::vector)) AS score
                    FROM memory_entries_active e
                    JOIN memory_entry_embeddings em ON em.entry_id = e.id
                    WHERE (%s::text IS NULL OR e.kind = %s::memory_kind)
                      AND (%s = '' OR e.domain = %s)
                    ORDER BY em.embedding <=> %s::vector
                    LIMIT %s
                """
                params: tuple[Any, ...] = (
                    vec,
                    kind.value if kind else None, kind.value if kind else None,
                    domain, domain, vec, limit,
                )
            else:
                sql = """
                    SELECT e.*, ts_rank(e.search_tsv, plainto_tsquery('simple', %s)) AS score
                    FROM memory_entries_active e
                    WHERE e.search_tsv @@ plainto_tsquery('simple', %s)
                      AND (%s::text IS NULL OR e.kind = %s::memory_kind)
                      AND (%s = '' OR e.domain = %s)
                    ORDER BY score DESC
                    LIMIT %s
                """
                params = (
                    query, query,
                    kind.value if kind else None, kind.value if kind else None,
                    domain, domain, limit,
                )
            with conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return [self._row_to_entry(r) for r in rows]

    def list_by_domain(self, domain: str) -> list[MemoryEntry]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM memory_entries_active WHERE domain = %s ORDER BY created_at DESC",
                    (domain,),
                )
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return [self._row_to_entry(r) for r in rows]

    def delete(self, entry_id: str) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM memory_entries WHERE id = %s", (entry_id,))
                deleted = cur.rowcount > 0
                if deleted:
                    cur.execute(
                        "INSERT INTO memory_audit_log (entry_id, action, actor) VALUES (%s, 'delete', 'system')",
                        (entry_id,),
                    )
        return deleted

    def all(self) -> list[MemoryEntry]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM memory_entries_active ORDER BY created_at DESC")
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return [self._row_to_entry(r) for r in rows]

    # ------------------------------------------------------------------
    # Synthesis API — matches FileMemoryStore surface
    # ------------------------------------------------------------------

    def get_synthesis(self, domain: str) -> dict | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM memory_syntheses WHERE domain = %s", (domain,))
                row = cur.fetchone()
                if not row:
                    return None
                cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def save_synthesis(
        self,
        domain: str,
        summary: str,
        key_themes: list[str],
        open_questions: list[str],
        synthesized_by: str = "ai",
    ) -> dict:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM memory_entries_active WHERE domain = %s",
                    (domain,),
                )
                entry_ids = [r[0] for r in cur.fetchall()]
                cur.execute(
                    """
                    INSERT INTO memory_syntheses
                        (domain, summary, key_themes, open_questions, synthesized_by,
                         entry_count_at_synthesis, entry_ids, stale, synthesized_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, now())
                    ON CONFLICT (domain) DO UPDATE SET
                        summary                  = EXCLUDED.summary,
                        key_themes               = EXCLUDED.key_themes,
                        open_questions           = EXCLUDED.open_questions,
                        synthesized_by           = EXCLUDED.synthesized_by,
                        entry_count_at_synthesis = EXCLUDED.entry_count_at_synthesis,
                        entry_ids                = EXCLUDED.entry_ids,
                        synthesized_at           = now(),
                        stale                    = FALSE
                    """,
                    (domain, summary, key_themes, open_questions, synthesized_by, len(entry_ids), entry_ids),
                )
        return {
            "summary": summary,
            "key_themes": key_themes,
            "open_questions": open_questions,
            "entry_count_at_synthesis": len(entry_ids),
            "entry_ids": entry_ids,
            "stale": False,
        }

    def synthesis_stale(self, domain: str) -> bool:
        syn = self.get_synthesis(domain)
        if not syn:
            return True
        if syn.get("stale"):
            return True
        with self._pool.connection() as conn:
            current = conn.execute(
                "SELECT COUNT(*) FROM memory_entries_active WHERE domain = %s", (domain,)
            ).fetchone()[0]
        return current != syn.get("entry_count_at_synthesis", 0)
