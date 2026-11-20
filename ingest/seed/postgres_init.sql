-- Zendesk-shaped support schema for local Postgres (Airbyte source).

CREATE TABLE IF NOT EXISTS accounts (
    account_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    industry     TEXT,
    arr          NUMERIC(14, 2) DEFAULT 0,
    plan_tier    TEXT,
    renewal_date DATE,
    status       TEXT DEFAULT 'active',
    owner_csm_id TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id    TEXT PRIMARY KEY,
    account_id   TEXT NOT NULL REFERENCES accounts(account_id),
    owner_csm_id TEXT NOT NULL,
    subject      TEXT NOT NULL,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'open',
    priority     TEXT NOT NULL DEFAULT 'normal',
    category     TEXT,
    sentiment    TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ticket_comments (
    comment_id   TEXT PRIMARY KEY,
    ticket_id    TEXT NOT NULL REFERENCES support_tickets(ticket_id),
    author_type  TEXT NOT NULL,
    body         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE SCHEMA IF NOT EXISTS airbyte_raw;

CREATE TABLE IF NOT EXISTS airbyte_raw.accounts (
    LIKE accounts INCLUDING ALL
);
ALTER TABLE airbyte_raw.accounts ADD COLUMN IF NOT EXISTS _airbyte_raw_id TEXT;
ALTER TABLE airbyte_raw.accounts ADD COLUMN IF NOT EXISTS _airbyte_extracted_at TIMESTAMPTZ;
ALTER TABLE airbyte_raw.accounts ADD COLUMN IF NOT EXISTS _airbyte_meta JSONB;

CREATE TABLE IF NOT EXISTS airbyte_raw.support_tickets (
    LIKE support_tickets INCLUDING ALL
);
ALTER TABLE airbyte_raw.support_tickets ADD COLUMN IF NOT EXISTS _airbyte_raw_id TEXT;
ALTER TABLE airbyte_raw.support_tickets ADD COLUMN IF NOT EXISTS _airbyte_extracted_at TIMESTAMPTZ;
ALTER TABLE airbyte_raw.support_tickets ADD COLUMN IF NOT EXISTS _airbyte_meta JSONB;

CREATE INDEX IF NOT EXISTS idx_tickets_owner ON support_tickets(owner_csm_id);
CREATE INDEX IF NOT EXISTS idx_tickets_account ON support_tickets(account_id);
CREATE INDEX IF NOT EXISTS idx_tickets_updated ON support_tickets(updated_at);
CREATE INDEX IF NOT EXISTS idx_accounts_updated ON accounts(updated_at);
