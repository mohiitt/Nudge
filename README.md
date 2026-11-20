# Nudge

Personal Customer Success agent for one CSM. Airbyte pulls sandbox sources into
SingleStore; Claude plans and acts with SIE for embeddings/ranking; Firedrill
drills synthetic tools; Amplitude measures outcomes.

## Architecture

```
Sandbox sources (Stripe test, HubSpot, Postgres, CSV)
        → Airbyte OSS
        → SingleStore (state + VECTOR memory)
        → FastAPI agent (Claude tool calling + SIE)
        → Next.js CSM console
Actions via gateway (HubSpot / Slack / email drafts) with env-overridable base URLs for Firedrill.
```

## Repository layout

| Path | Role |
|------|------|
| `apps/web` | Next.js CSM console |
| `services/agent` | FastAPI agent backend |
| `data/generator` | RavenStack + synthetic augmentation |
| `ingest` | Airbyte configs, seed scripts, PG→S2 loader |
| `db/singlestore` | Schema, views, scoring |
| `evals/firedrill` | Reliability drills |
| `docs/` | Credentials, events, demo |

Shared contracts: `services/agent/app/contracts.py`, `db/singlestore/schema.sql`,
`.cursor/rules/contracts.mdc`.

## Prerequisites

- Python 3.11+
- Node 22+
- Docker (for local Postgres)
- Optional live: Anthropic, SingleStore Helios, SIE, Amplitude, HubSpot, Stripe — see [docs/CREDENTIALS.md](docs/CREDENTIALS.md)

## Quick start (mocked)

```bash
cp .env.example .env
# MOCK_MODE=true is the default

# Postgres for support seed
docker compose up -d postgres

# Agent
cd services/agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Web (another terminal)
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000. Agent health: http://localhost:8000/health.

Firedrill-compatible chat:

```bash
curl -s http://localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"What needs attention today?","session":"demo"}'
```

## Full stack (compose profile)

```bash
docker compose --profile full up --build
```

## Credentials

Step-by-step for every `.env` variable: [docs/CREDENTIALS.md](docs/CREDENTIALS.md).  
Amplitude events: [docs/events.md](docs/events.md).  
Demo walkthrough: [docs/DEMO.md](docs/DEMO.md).  
Firedrill event code: **TOKENSAND**.

## Seed data

```bash
python3 data/generator/generate.py
docker compose up -d postgres
# optional: pip install psycopg httpx && python ingest/seed/seed_postgres.py
```

## Hard rules

1. Ownership always enforced: `owner_csm_id = :csm_id` on every data query.
2. Sensitive actions always create `approval_requests`.
3. Never send real external email — drafts only pending approval.
