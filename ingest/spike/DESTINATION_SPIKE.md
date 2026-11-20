# Airbyte → SingleStore destination spike

Timeboxed verification of how Airbyte writes into SingleStore Helios.
SingleStore speaks the MySQL wire protocol (port 3306), so the preferred path
is the stock **MySQL destination**, not a SingleStore-specific connector.

## Prerequisites

- SingleStore Helios workspace reachable on port 3306
- Firewall allowlist includes your IP
- Database `nudge` created; apply `db/singlestore/schema.sql` for core tables
- Dedicated `airbyte` DB user with grants:

  ```sql
  GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER
    ON nudge.* TO 'airbyte'@'%';
  FLUSH PRIVILEGES;
  ```

- **Critical for LOAD DATA / bulk load:**

  ```sql
  SET GLOBAL local_infile = true;
  ```

  Confirm:

  ```sql
  SHOW GLOBAL VARIABLES LIKE 'local_infile';
  -- Value should be ON
  ```

## Path A (preferred): Airbyte MySQL destination → SingleStore

1. In Airbyte UI, add destination **MySQL**.
2. Connection settings:
   - Host: `SINGLESTORE_HOST`
   - Port: `3306`
   - Database: `nudge` (or a dedicated raw schema DB, e.g. `nudge_raw`)
   - Username / password: the `airbyte` user
   - SSL: as required by Helios (typically required)
   - JDBC URL params (if exposed): `allowLoadLocalInfile=true`
3. Point a trivial source (e.g. sample data or local Postgres) at this destination.
4. Run a sync; verify rows land and `_airbyte_*` metadata columns exist.

### Expected failure modes

| Symptom | Likely cause | Mitigation |
|---------|--------------|------------|
| `LOAD DATA LOCAL` / infile errors | `local_infile` off | `SET GLOBAL local_infile = true` |
| Auth / SSL handshake fail | Helios SSL or IP allowlist | Fix firewall; enable SSL |
| Slow / timeout on large sync | Workspace size / network | Smaller batches; suspend-aware retries |
| Destination rejects VECTOR/JSON DDL | Raw tables ≠ core schema | Sync into raw tables; transform via loader/views |

### Spike checklist

- [ ] `local_infile` ON
- [ ] MySQL destination connected
- [ ] One stream sync succeeds (accounts or tickets)
- [ ] Incremental cursor works (`updated_at` or `_airbyte_extracted_at`)

If Path A works for incremental syncs, **stop here** and use it in production configs
under `ingest/airbyte/`.

## Path B: archived `destination-singlestore`

Airbyte's native SingleStore destination is **archived**. It may still run as a
custom Docker connector image for a short verification:

```bash
# Example only — image tags change; verify on Docker Hub / GHCR before use
docker pull airbyte/destination-singlestore:0.1.4
```

In Airbyte OSS (`abctl`):

1. Settings → Destinations → add **Custom** / Docker connector.
2. Image: `airbyte/destination-singlestore:<tag>`
3. Configure host/port/user/password/database like Path A.
4. Re-run the same trivial sync.

### When to abandon Path B

- Image unavailable or fails to start under current Airbyte protocol version
- Spec / discover fails against Helios
- Sync succeeds but columns / typing are unusable for our schema

Document the outcome in the spike log (`ingest/spike/spike_log.md` after a run).

## Path C (final fallback): Airbyte → Postgres → `pg_to_s2.py`

1. Configure Airbyte destinations to **local Postgres** (`docker compose` service
   `postgres`, DB `nudge_support` or a dedicated `nudge_airbyte` schema).
2. Sources (HubSpot, Stripe, CSV, Zendesk-shaped Postgres) sync into Postgres.
3. Run the incremental loader:

   ```bash
   python ingest/loader/pg_to_s2.py
   # or dry-run without SingleStore credentials:
   MOCK_MODE=true python ingest/loader/pg_to_s2.py
   ```

4. Watermark key: prefer `_airbyte_extracted_at`, else `updated_at`.
   State is stored in `ingest/loader/.sync_state.json` (gitignored pattern).

This path is fully mockable and is the default for local demos without Helios.

## Recommended decision order

```
1. Try Path A (MySQL dest + local_infile)
2. If blocked by connector protocol / Helios quirks → Path B (archived image)
3. If still blocked → Path C (Postgres + pg_to_s2.py)  ← always available
```

## Helper scripts

| Script | Purpose |
|--------|---------|
| `check_local_infile.py` | Connect to S2 and report `local_infile` |
| `enable_local_infile.sql` | SQL to enable + verify |
| `run_spike.sh` | Orchestrates checks and prints next steps |

## Related files

- `ingest/airbyte/` — connection stubs for all three paths
- `ingest/loader/pg_to_s2.py` — Path C loader
- `docs/CREDENTIALS.md` — SingleStore + Airbyte credential steps
