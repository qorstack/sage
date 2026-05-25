# Test Guide

End-to-end test for the Postgres + dashboard stack. Should take ~5 minutes.

> Knowledge is stored in **Postgres** (not git anymore). No `tutorial-knowlyx-knowledge` repo needed.

## 1. Start the stack

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps        # both knowai-postgres and knowai-web should be healthy
```

## 2. Verify it's alive

```bash
curl -s http://localhost:8080/healthz
# → {"status":"ok"}

docker exec knowai-postgres psql -U knowai -d knowai -c "\dt"
# → memory_entries, memory_entry_embeddings, memory_syntheses, memory_audit_log
```

Open <http://localhost:8080> — Overview loads with all counts at 0.

## 3. Add the first knowledge entry

Open <http://localhost:8080/knowledge>:

1. Sign in as `alice` (sticky cookie for audit log).
2. Add an entry:
   - Kind: `team_decision`
   - Domain: `payment`
   - Title: `Use idempotency keys for all payment calls`
   - Body: `Every POST /payments must include an Idempotency-Key header. Server stores keys for 24h to dedupe retries.`
   - Tags: `payment, api, idempotency`
   - ☑ Auto-approve
3. Submit.

**Check:** Overview now shows `Active = 1`, `Approved = 1`, `Events (24h) = 1`.

## 4. Verify auto-merge (the important one)

Add a second entry, same domain, similar topic:

- Kind: `team_decision`
- Domain: `payment`
- Title: `Idempotency-Key header is mandatory for payment endpoints`
- Body: `All POST /payments endpoints require an Idempotency-Key header to safely retry. Keys are kept for 24 hours.`
- Tags: `payment, api`

**Expected:** after submit, you land on the **original** entry's detail page (not a new one).

**Check on the detail page:**
- "Merged 1 time(s)" appears in Metadata.
- A `contributors` row lists the second entry's title + actor `alice`.
- Body shows the new content appended after a `---` separator.
- Audit log has both `insert` and `merge` rows.
- Overview still shows `Active = 1` — the merge prevented a duplicate.

If you get **two separate entries** instead, the embedding model didn't load. Run `docker compose logs web | grep -i sentence` to confirm.

## 5. Edit / Approve / Delete

On any entry's detail page:

- **Edit** → change the body → audit log gets `update`.
- **Approve** (if pending) → status flips to `approved`, audit log gets `approve`.
- **Delete** → entry removed from `/entries`, audit log keeps the `delete` row.

## 6. Check syntheses (domain-level summary)

```sql
docker exec knowai-postgres psql -U knowai -d knowai \
  -c "SELECT domain, stale FROM memory_syntheses;"
```

Empty initially — syntheses are created by AI (via MCP `save_synthesis`), not the dashboard. The `stale` flag flips to `true` automatically whenever an entry in that domain changes, so the AI knows to re-summarize.

Visit <http://localhost:8080/syntheses> — shows "No syntheses yet" until the AI writes one.

## 7. Tear down

```bash
docker compose down       # stop, keep data
docker compose down -v    # also wipe the Postgres volume
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `web` container unhealthy | Postgres not ready yet — `docker compose logs web` and retry after 10s |
| `RuntimeError: Missing required env vars` | `.env` missing — `cp .env.example .env` |
| Two entries created instead of merging | Embedding model failed to load. Check `docker compose logs web` for `sentence-transformers` errors. Without embeddings only exact-title matches dedupe. |
| Dashboard shows stale data after schema change | `docker compose restart web` to reset the connection pool |
| Port `5432` or `8080` already in use | Change `POSTGRES_PORT` or `WEB_PORT` in `.env` |
