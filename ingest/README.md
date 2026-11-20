# Ingest

1. Generate data: `python -m data.generator`
2. Start Postgres: `docker compose up -d postgres`
3. Seed: `python ingest/seed/seed_postgres.py`
4. Optional: `seed_stripe.py`, `seed_hubspot.py`, `seed_csv.py`
5. Destination spike notes: `ingest/spike/DESTINATION_SPIKE.md`
6. Fallback loader: `python ingest/loader/pg_to_s2.py` (dry-run without S2 creds)

Airbyte stubs: `ingest/airbyte/connections.yaml`.
