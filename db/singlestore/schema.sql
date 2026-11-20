-- Nudge SingleStore schema
-- MySQL-compatible; VECTOR + ANN + full-text where noted.
-- Run against SingleStore Helios (port 3306) after creating the database.

CREATE DATABASE IF NOT EXISTS nudge;
USE nudge;

-- ---------------------------------------------------------------------------
-- Identity and personalization
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS csms (
    csm_id          VARCHAR(64)  NOT NULL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    timezone        VARCHAR(64)  NOT NULL DEFAULT 'America/Los_Angeles',
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS csm_preferences (
    csm_id          VARCHAR(64)  NOT NULL PRIMARY KEY,
    preferred_channel ENUM('email','call','slack','linkedin') NOT NULL DEFAULT 'email',
    briefing_hour_local TINYINT UNSIGNED NOT NULL DEFAULT 8,
    risk_threshold  DECIMAL(5,2) NOT NULL DEFAULT 0.60,
    prefs_json      JSON,
    updated_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    SHARD KEY (csm_id),
    FOREIGN KEY (csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS approval_policies (
    policy_id       VARCHAR(64)  NOT NULL PRIMARY KEY,
    csm_id          VARCHAR(64)  NOT NULL,
    action_type     VARCHAR(64)  NOT NULL,
    requires_approval TINYINT(1) NOT NULL DEFAULT 1,
    max_auto_amount DECIMAL(12,2) NULL,
    notes           VARCHAR(512) NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    SHARD KEY (csm_id),
    KEY (csm_id, action_type),
    FOREIGN KEY (csm_id) REFERENCES csms(csm_id)
);

-- ---------------------------------------------------------------------------
-- Business state
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS accounts (
    account_id      VARCHAR(64)  NOT NULL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    industry        VARCHAR(128) NULL,
    arr             DECIMAL(14,2) NOT NULL DEFAULT 0,
    plan_tier       VARCHAR(64)  NULL,
    renewal_date    DATE         NULL,
    health_score    DECIMAL(5,2) NULL,
    status          ENUM('active','churn_risk','churned','expansion') NOT NULL DEFAULT 'active',
    owner_csm_id    VARCHAR(64)  NOT NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    SHARD KEY (account_id),
    KEY (owner_csm_id),
    FOREIGN KEY (owner_csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS account_ownership (
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    effective_from  DATE         NOT NULL,
    effective_to    DATE         NULL,
    PRIMARY KEY (account_id, owner_csm_id, effective_from),
    SHARD KEY (account_id),
    KEY (owner_csm_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (owner_csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    stripe_sub_id   VARCHAR(128) NULL,
    plan_name       VARCHAR(128) NOT NULL,
    mrr             DECIMAL(12,2) NOT NULL DEFAULT 0,
    seats           INT          NOT NULL DEFAULT 1,
    status          ENUM('active','past_due','canceled','trialing') NOT NULL DEFAULT 'active',
    started_at      DATE         NOT NULL,
    ends_at         DATE         NULL,
    SHARD KEY (account_id),
    KEY (account_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE IF NOT EXISTS invoices_payments (
    invoice_id      VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    stripe_invoice_id VARCHAR(128) NULL,
    amount          DECIMAL(12,2) NOT NULL,
    currency        CHAR(3)      NOT NULL DEFAULT 'USD',
    status          ENUM('paid','open','void','uncollectible','failed') NOT NULL,
    due_date        DATE         NULL,
    paid_at         DATETIME(6)  NULL,
    failure_reason  VARCHAR(255) NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    SHARD KEY (account_id),
    KEY (account_id, status),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Columnstore for analytics over daily usage
CREATE TABLE IF NOT EXISTS usage_daily (
    account_id      VARCHAR(64)  NOT NULL,
    usage_date      DATE         NOT NULL,
    dau             INT          NOT NULL DEFAULT 0,
    sessions        INT          NOT NULL DEFAULT 0,
    events          INT          NOT NULL DEFAULT 0,
    feature_events  INT          NOT NULL DEFAULT 0,
    SORT KEY (usage_date, account_id),
    SHARD KEY (account_id),
    KEY (account_id, usage_date)
);

CREATE TABLE IF NOT EXISTS feature_adoption (
    account_id      VARCHAR(64)  NOT NULL,
    feature_name    VARCHAR(128) NOT NULL,
    first_used_at   DATETIME(6)  NULL,
    last_used_at    DATETIME(6)  NULL,
    use_count_30d   INT          NOT NULL DEFAULT 0,
    adoption_pct    DECIMAL(5,2) NULL,
    PRIMARY KEY (account_id, feature_name),
    SHARD KEY (account_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id       VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    subject         VARCHAR(512) NOT NULL,
    status          ENUM('open','pending','solved','closed') NOT NULL DEFAULT 'open',
    priority        ENUM('low','normal','high','urgent') NOT NULL DEFAULT 'normal',
    category        VARCHAR(128) NULL,
    sentiment       VARCHAR(32)  NULL,
    created_at      DATETIME(6)  NOT NULL,
    updated_at      DATETIME(6)  NOT NULL,
    resolved_at     DATETIME(6)  NULL,
    SHARD KEY (account_id),
    KEY (owner_csm_id, status),
    KEY (account_id, created_at),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (owner_csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS crm_activities (
    activity_id     VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    activity_type   ENUM('note','call','email','meeting','task') NOT NULL,
    subject         VARCHAR(512) NULL,
    body            TEXT,
    hubspot_id      VARCHAR(128) NULL,
    occurred_at     DATETIME(6)  NOT NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    SHARD KEY (account_id),
    KEY (owner_csm_id, occurred_at),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (owner_csm_id) REFERENCES csms(csm_id)
);

-- ---------------------------------------------------------------------------
-- Derived state
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS account_health_snapshots (
    snapshot_id     BIGINT       NOT NULL AUTO_INCREMENT,
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    snapshot_at     DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    health_score    DECIMAL(5,2) NOT NULL,
    risk_score      DECIMAL(5,2) NOT NULL,
    usage_delta_30d DECIMAL(8,4) NULL,
    open_tickets    INT          NOT NULL DEFAULT 0,
    days_to_renewal INT          NULL,
    failed_payments INT          NOT NULL DEFAULT 0,
    reasons_json    JSON,
    PRIMARY KEY (snapshot_id),
    SHARD KEY (account_id),
    KEY (owner_csm_id, snapshot_at),
    KEY (account_id, snapshot_at),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE OR REPLACE VIEW v_usage_delta_30d AS
SELECT
    u.account_id,
    SUM(CASE WHEN u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
             THEN u.events ELSE 0 END) AS events_last_30d,
    SUM(CASE WHEN u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
              AND u.usage_date <  DATE_SUB(CURDATE(), INTERVAL 30 DAY)
             THEN u.events ELSE 0 END) AS events_prev_30d,
    CASE
        WHEN SUM(CASE WHEN u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                       AND u.usage_date <  DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                      THEN u.events ELSE 0 END) = 0 THEN NULL
        ELSE (
            SUM(CASE WHEN u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                     THEN u.events ELSE 0 END)
            - SUM(CASE WHEN u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                        AND u.usage_date <  DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                       THEN u.events ELSE 0 END)
        ) / SUM(CASE WHEN u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                      AND u.usage_date <  DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                     THEN u.events ELSE 0 END)
    END AS usage_delta_30d
FROM usage_daily u
WHERE u.usage_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
GROUP BY u.account_id;

CREATE OR REPLACE VIEW v_account_risk_signals AS
SELECT
    a.account_id,
    a.owner_csm_id,
    a.name,
    a.arr,
    a.renewal_date,
    COALESCE(d.usage_delta_30d, 0) AS usage_delta_30d,
    COALESCE(t.open_tickets, 0) AS open_tickets,
    DATEDIFF(a.renewal_date, CURDATE()) AS days_to_renewal,
    COALESCE(p.failed_payments, 0) AS failed_payments,
    (
        GREATEST(0, -COALESCE(d.usage_delta_30d, 0)) * 0.35
        + LEAST(COALESCE(t.open_tickets, 0) / 5.0, 1.0) * 0.25
        + CASE
            WHEN DATEDIFF(a.renewal_date, CURDATE()) IS NULL THEN 0
            WHEN DATEDIFF(a.renewal_date, CURDATE()) <= 30 THEN 0.25
            WHEN DATEDIFF(a.renewal_date, CURDATE()) <= 60 THEN 0.15
            ELSE 0
          END
        + LEAST(COALESCE(p.failed_payments, 0) / 2.0, 1.0) * 0.15
    ) AS risk_score
FROM accounts a
LEFT JOIN v_usage_delta_30d d ON d.account_id = a.account_id
LEFT JOIN (
    SELECT account_id, COUNT(*) AS open_tickets
    FROM support_tickets
    WHERE status IN ('open', 'pending')
    GROUP BY account_id
) t ON t.account_id = a.account_id
LEFT JOIN (
    SELECT account_id, COUNT(*) AS failed_payments
    FROM invoices_payments
    WHERE status IN ('failed', 'uncollectible')
      AND created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
    GROUP BY account_id
) p ON p.account_id = a.account_id
WHERE a.status IN ('active', 'churn_risk', 'expansion');

-- ---------------------------------------------------------------------------
-- Semantic / embeddings (VECTOR dim matches Qwen3-Embedding-4B truncated/projected to 2560)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ticket_chunks (
    chunk_id        VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    ticket_id       VARCHAR(64)  NOT NULL,
    category        VARCHAR(128) NULL,
    sentiment       VARCHAR(32)  NULL,
    created_at      DATETIME(6)  NOT NULL,
    text_redacted   TEXT         NOT NULL,
    embedding       VECTOR(2560),
    SHARD KEY (account_id),
    KEY (owner_csm_id, created_at),
    KEY (ticket_id),
    FULLTEXT (text_redacted),
    VECTOR INDEX ann_ticket_embedding (embedding) INDEX_OPTIONS '{"index_type":"IVF_PQFS","metric_type":"DOT_PRODUCT"}',
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id)
);

CREATE TABLE IF NOT EXISTS playbook_chunks (
    chunk_id        VARCHAR(64)  NOT NULL PRIMARY KEY,
    playbook_name   VARCHAR(255) NOT NULL,
    category        VARCHAR(128) NULL,
    text_redacted   TEXT         NOT NULL,
    embedding       VECTOR(2560),
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FULLTEXT (text_redacted),
    VECTOR INDEX ann_playbook_embedding (embedding) INDEX_OPTIONS '{"index_type":"IVF_PQFS","metric_type":"DOT_PRODUCT"}'
);

CREATE TABLE IF NOT EXISTS intervention_embeddings (
    intervention_id VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    summary_text    TEXT         NOT NULL,
    outcome         VARCHAR(64)  NULL,
    embedding       VECTOR(2560),
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    SHARD KEY (account_id),
    KEY (owner_csm_id),
    VECTOR INDEX ann_intervention_embedding (embedding) INDEX_OPTIONS '{"index_type":"IVF_PQFS","metric_type":"DOT_PRODUCT"}',
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- ---------------------------------------------------------------------------
-- Agent memory, interventions, audit, approvals
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS agent_memory (
    memory_id       VARCHAR(64)  NOT NULL PRIMARY KEY,
    csm_id          VARCHAR(64)  NOT NULL,
    account_id      VARCHAR(64)  NULL,
    memory_type     ENUM('preference','fact','outcome','note') NOT NULL,
    content         TEXT         NOT NULL,
    embedding       VECTOR(2560),
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    expires_at      DATETIME(6)  NULL,
    SHARD KEY (csm_id),
    KEY (csm_id, account_id),
    FOREIGN KEY (csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS interventions (
    intervention_id VARCHAR(64)  NOT NULL PRIMARY KEY,
    account_id      VARCHAR(64)  NOT NULL,
    owner_csm_id    VARCHAR(64)  NOT NULL,
    action_type     VARCHAR(64)  NOT NULL,
    summary         TEXT         NOT NULL,
    plan_json       JSON,
    outcome         ENUM('pending','improved','unchanged','worsened','unknown') NOT NULL DEFAULT 'pending',
    outcome_measured_at DATETIME(6) NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    SHARD KEY (account_id),
    KEY (owner_csm_id, created_at),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (owner_csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS agent_actions (
    action_id       VARCHAR(64)  NOT NULL PRIMARY KEY,
    csm_id          VARCHAR(64)  NOT NULL,
    account_id      VARCHAR(64)  NULL,
    action_type     VARCHAR(64)  NOT NULL,
    tool_name       VARCHAR(128) NOT NULL,
    request_json    JSON,
    response_json   JSON,
    status          ENUM('proposed','approved','rejected','executed','failed','skipped') NOT NULL,
    approval_id     VARCHAR(64)  NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    executed_at     DATETIME(6)  NULL,
    SHARD KEY (csm_id),
    KEY (account_id, created_at),
    KEY (status),
    FOREIGN KEY (csm_id) REFERENCES csms(csm_id)
);

CREATE TABLE IF NOT EXISTS approval_requests (
    approval_id     VARCHAR(64)  NOT NULL PRIMARY KEY,
    csm_id          VARCHAR(64)  NOT NULL,
    account_id      VARCHAR(64)  NULL,
    action_type     VARCHAR(64)  NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT,
    payload_json    JSON         NOT NULL,
    status          ENUM('pending','approved','rejected','expired') NOT NULL DEFAULT 'pending',
    decided_by      VARCHAR(64)  NULL,
    decided_at      DATETIME(6)  NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    expires_at      DATETIME(6)  NULL,
    SHARD KEY (csm_id),
    KEY (csm_id, status),
    FOREIGN KEY (csm_id) REFERENCES csms(csm_id)
);

-- Embedding cache: avoid re-embedding unchanged content
CREATE TABLE IF NOT EXISTS embedding_cache (
    content_hash    CHAR(64)     NOT NULL PRIMARY KEY,
    model           VARCHAR(128) NOT NULL,
    embedding       VECTOR(2560) NOT NULL,
    created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    KEY (model)
);
