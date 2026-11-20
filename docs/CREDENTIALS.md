# Credentials setup guide

Fill `.env` from `.env.example`. Nothing in this repo requires live secrets to
**write or run mocked local demos**. Credentials below are needed for live
SingleStore, SIE, Amplitude, HubSpot, Stripe, Airbyte, and Claude.

---

## 1. Anthropic (`ANTHROPIC_API_KEY`)

1. Go to [console.anthropic.com](https://console.anthropic.com).
2. Open **Settings → API Keys**.
3. Create a key and set `ANTHROPIC_API_KEY=sk-ant-...`.
4. Optional: `ANTHROPIC_MODEL=claude-sonnet-4-20250514` (or your preferred model).

---

## 2. SingleStore Helios

Vars: `SINGLESTORE_HOST`, `SINGLESTORE_PORT`, `SINGLESTORE_USER`,
`SINGLESTORE_PASSWORD`, `SINGLESTORE_DATABASE`.

1. Create a workspace in the Helios portal (smallest / shared tier is fine).
2. Open **Connect → Your App**. Use port **3306** (MySQL protocol).
3. Add your IP to the firewall allowlist.
4. Create database `nudge` (or set `SINGLESTORE_DATABASE`).
5. Apply `db/singlestore/schema.sql`.
6. Create a separate `airbyte` user with grants suitable for Airbyte MySQL
   destination (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`,
   `INDEX`, `ALTER` on the target DB). Enable `SET GLOBAL local_infile = true`
   if using LOAD DATA.

Suspend the workspace when idle to save credits.

---

## 3. SIE Serverless (Superlinked)

Vars: `SIE_API_KEY`, `SIE_BASE_URL`.

1. Open the Superlinked Serverless console → **API keys**.
2. Copy a key (`sk-sie-...`) into `SIE_API_KEY`.
3. Set `SIE_BASE_URL=https://api.superlinked.com`.

Models used by Nudge:

| Capability | Model |
|------------|--------|
| Embed | `Qwen/Qwen3-Embedding-4B` |
| Rerank / score | `Qwen/Qwen3-Reranker-4B` |
| Classify | `knowledgator/gliclass-large-v3.0` |
| Extract | `fastino/gliner2-large-v1` |
| Redact | `numind/NuNER_Zero` |

Cache embeddings in SingleStore (`embedding_cache`) and never re-embed unchanged rows.

---

## 4. Amplitude

Vars: `AMPLITUDE_API_KEY`, optional `AMPLITUDE_SECRET_KEY`.

1. Amplitude → **Settings → Projects → [project] → General → API Key**.
2. Set `AMPLITUDE_API_KEY`.
3. `AMPLITUDE_SECRET_KEY` is only needed for Export API / Airbyte Amplitude source.
4. Free plan: **max 10 events per HTTP V2 request**. See `docs/events.md`.

---

## 5. HubSpot (free developer account)

Var: `HUBSPOT_ACCESS_TOKEN`. Base URL override: `HUBSPOT_BASE_URL`
(default `https://api.hubapi.com`; Firedrill redirects this).

1. Create a free HubSpot developer account and a test account.
2. Create a **Private App** with scopes: contacts, companies, deals, tickets,
   tasks, notes.
3. Copy the access token to `HUBSPOT_ACCESS_TOKEN`.

---

## 6. Stripe (test mode)

Var: `STRIPE_SECRET_KEY` (`sk_test_...`). Override: `STRIPE_BASE_URL`
(default `https://api.stripe.com`).

1. Stripe Dashboard → enable **Test mode**.
2. **Developers → API keys** → copy Secret key.

---

## 7. Kaggle (RavenStack dataset)

Vars: `KAGGLE_USERNAME`, `KAGGLE_KEY`.

1. Kaggle → **Settings → Create New Token** (downloads `kaggle.json`).
2. Set username and key from that file.
3. Dataset:
   `https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset`
4. If download fails, `data/generator` produces RavenStack-shaped synthetic CSVs.

---

## 8. Local Postgres (Docker Compose)

Vars: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB`.

Defaults in `docker-compose.yml`:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nudge
POSTGRES_PASSWORD=nudge
POSTGRES_DB=nudge_support
```

Used for Zendesk-shaped support tickets / accounts seed for Airbyte.

---

## 9. Airbyte OSS (`abctl`)

Vars: `AIRBYTE_URL`, `AIRBYTE_CLIENT_ID`, `AIRBYTE_CLIENT_SECRET`.

1. Install `abctl` and run `abctl local install`.
2. Run `abctl local credentials` and copy URL / client id / secret.
3. Destination spike: MySQL destination → SingleStore; fallback Airbyte →
   local Postgres → `ingest/loader/pg_to_s2.py`.

---

## 10. Slack (optional)

Var: `SLACK_BOT_TOKEN`. Override: `SLACK_BASE_URL`.

1. Create a Slack app with `chat:write`.
2. Install to a test workspace and copy the bot token (`xoxb-...`).

---

## 11. Action Gateway base URLs (Firedrill)

These default to real APIs. Firedrill overrides them per run:

| Variable | Default |
|----------|---------|
| `HUBSPOT_BASE_URL` | `https://api.hubapi.com` |
| `STRIPE_BASE_URL` | `https://api.stripe.com` |
| `GMAIL_BASE_URL` | `https://gmail.googleapis.com` |
| `SLACK_BASE_URL` | `https://slack.com/api` |

**Never send real external email.** Drafts only, pending approval.

---

## 12. Firedrill (no `.env` key)

1. Node **22, 24, or 26** only: `npm i -g firedrill-run`.
2. `firedrill init` (browser sign-in).
3. Add MCP server `https://mcp.firedrill.run` in Cursor.
4. `npx skills add firedrill-tools/firedrill-skills`.
5. Apply event code **`TOKENSAND`** under Billing for extra non-expiring credits.
6. Review credit estimate before each `firedrill apply`.

Local plan drives `http.v1` against agent `POST /chat`
(`{"message","session"}` → `{"reply"}`).

---

## 13. App runtime

| Variable | Purpose |
|----------|---------|
| `AGENT_HOST` / `AGENT_PORT` | FastAPI bind (default `0.0.0.0:8000`) |
| `DEFAULT_CSM_ID` | Demo CSM id when session omits it |
| `WEB_ORIGIN` | CORS origin for Next.js (default `http://localhost:3000`) |
| `MOCK_MODE` | `true` to use in-memory mocks when secrets missing |

---

## Quick checklist

- [ ] `ANTHROPIC_API_KEY`
- [ ] SingleStore connect + schema applied
- [ ] `SIE_API_KEY`
- [ ] `AMPLITUDE_API_KEY`
- [ ] HubSpot private app token
- [ ] Stripe `sk_test_...`
- [ ] Kaggle token (or use synthetic generator)
- [ ] Postgres via `docker compose up -d postgres`
- [ ] Airbyte `abctl local credentials`
- [ ] Firedrill installed + `TOKENSAND` applied
- [ ] Optional Slack bot token
