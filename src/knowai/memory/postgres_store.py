"""
Postgres-backed memory store with auto-bootstrap (zero setting).

Activated when POSTGRES_USER env is set. DSN is built from POSTGRES_USER,
POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB — no separate
KNOWAI_DB_URL needed.

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

from knowai.memory.schema import MemoryEntry, MemoryKind
from knowai.memory.store import MemoryStore

DEFAULT_SCHEMA = "public"
# Cosine similarity above which a new entry is merged into an existing one.
# Hard-coded to keep configuration zero-touch; tune in code if needed.
SIMILARITY_THRESHOLD = 0.92


def _validate_schema_name(name: str) -> str:
    """Allow only safe identifier chars — schema name is interpolated into DDL."""
    if not name or not all(c.isalnum() or c == "_" for c in name):
        raise ValueError(f"Invalid schema name: {name!r}")
    return name


def _build_dsn_from_env() -> str:
    """Compose DSN from POSTGRES_* env vars. Fails loud if any required var is missing."""
    from urllib.parse import quote_plus

    required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing required env vars: {', '.join(missing)}. "
            "Define them in .env (see .env.example)."
        )
    user = quote_plus(os.environ["POSTGRES_USER"])
    pw = quote_plus(os.environ["POSTGRES_PASSWORD"])
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_DB"]
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"


def _load_schema_sql() -> str:
    return resources.files("knowai.memory.sql").joinpath("schema.sql").read_text(encoding="utf-8")


class PostgresMemoryStore(MemoryStore):
    """Postgres + pgvector store. Bootstraps schema on first connect."""

    def __init__(self, dsn: str = "", schema: str = "") -> None:
        import psycopg
        from psycopg_pool import ConnectionPool

        self._dsn = dsn or _build_dsn_from_env()
        self._schema = _validate_schema_name(
            schema or os.getenv("POSTGRES_SCHEMA") or DEFAULT_SCHEMA
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
        """
        Append-merge save:

        - Same (kind, domain, title) → same id → update in-place (no merge needed)
        - Different title but cosine similarity ≥ threshold → merge new body
          into the existing canonical entry (append, union tags, contributor log)
        - Otherwise → insert fresh

        Race condition is prevented by pg_advisory_xact_lock(domain) inside a
        single transaction, so two concurrent saves in the same domain serialize.
        """
        import hashlib

        if not entry.id:
            key = f"{entry.kind.value}:{entry.domain}:{entry.title}"
            entry.id = hashlib.sha256(key.encode()).hexdigest()[:16]

        vec = self._encode(f"{entry.title} {entry.body}")

        with self._pool.connection() as conn, conn.transaction():
            with conn.cursor() as cur:
                # Per-domain advisory lock — serializes save() calls for the
                # same domain. Released automatically at COMMIT.
                cur.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)",
                    (entry.domain,),
                )

                canonical_id = self._find_canonical(cur, entry, vec)
                if canonical_id and canonical_id != entry.id:
                    self._merge_into(cur, canonical_id, entry)
                    entry.id = canonical_id
                else:
                    self._insert_or_update(cur, entry)

                if vec is not None:
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

        return entry

    # ------------------------------------------------------------------
    # save() helpers
    # ------------------------------------------------------------------

    def _find_canonical(self, cur, entry: MemoryEntry, vec: list[float] | None) -> str | None:
        """Return the id of an existing entry to merge into, or None."""
        # 1. Exact id match (same kind+domain+title) → not a merge candidate,
        #    handled by _insert_or_update's ON CONFLICT.
        cur.execute(
            "SELECT id FROM memory_entries WHERE id = %s AND superseded_by IS NULL",
            (entry.id,),
        )
        if cur.fetchone():
            return entry.id

        # 2. Similar embedding in same domain.
        if vec is None:
            return None
        cur.execute(
            """
            SELECT id
            FROM memory_entries e
            JOIN memory_entry_embeddings em ON em.entry_id = e.id
            WHERE e.domain = %s
              AND e.superseded_by IS NULL
              AND (1 - (em.embedding <=> %s::vector)) >= %s
            ORDER BY em.embedding <=> %s::vector
            LIMIT 1
            """,
            (entry.domain, vec, SIMILARITY_THRESHOLD, vec),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def _insert_or_update(self, cur, entry: MemoryEntry) -> None:
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
            RETURNING (xmax = 0) AS inserted
            """,
            (
                entry.id, entry.kind.value, entry.domain, entry.title, entry.body,
                entry.tags, entry.approved, entry.approved_by, entry.repo_path,
                json.dumps(entry.metadata, default=str),
            ),
        )
        inserted = cur.fetchone()[0]
        action = "insert" if inserted else "update"
        cur.execute(
            "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, %s, %s, %s::jsonb)",
            (entry.id, action, entry.approved_by or "system", json.dumps({"title": entry.title})),
        )

    def _merge_into(self, cur, canonical_id: str, incoming: MemoryEntry) -> None:
        """Append incoming body to the canonical entry, union tags, log contributor."""
        from datetime import datetime, timezone

        separator = f"\n\n---\n[merge {datetime.now(timezone.utc).isoformat()} from \"{incoming.title}\"]\n"
        contributor = {
            "title": incoming.title,
            "actor": incoming.approved_by or "system",
            "at": datetime.now(timezone.utc).isoformat(),
        }
        cur.execute(
            """
            UPDATE memory_entries
            SET body     = body || %s,
                tags     = ARRAY(SELECT DISTINCT x FROM unnest(tags || %s) AS x),
                metadata = jsonb_set(
                    jsonb_set(
                        metadata,
                        '{contributors}',
                        COALESCE(metadata->'contributors', '[]'::jsonb) || %s::jsonb,
                        true
                    ),
                    '{merge_count}',
                    to_jsonb(COALESCE((metadata->>'merge_count')::int, 0) + 1),
                    true
                )
            WHERE id = %s
            """,
            (
                separator + incoming.body,
                incoming.tags or [],
                json.dumps([contributor]),
                canonical_id,
            ),
        )
        cur.execute(
            "INSERT INTO memory_audit_log (entry_id, action, actor, diff) VALUES (%s, 'merge', %s, %s::jsonb)",
            (
                canonical_id,
                incoming.approved_by or "system",
                json.dumps({"merged_from_title": incoming.title, "merged_from_id": incoming.id}),
            ),
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
