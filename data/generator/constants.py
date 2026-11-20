"""Shared constants for the Nudge data generator."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "ravenstack"
OUTPUT_DIR = DATA_DIR / "output"
FIXTURES_DIR = DATA_DIR / "fixtures"

KAGGLE_DATASET = "rivalytics/saas-subscription-and-churn-analytics-dataset"

# Demo CSMs — must match contracts / .env.example DEFAULT_CSM_ID
CSM_DEMO = {
    "csm_id": "csm_demo_001",
    "email": "alex@nudge.local",
    "full_name": "Alex Rivera",
    "timezone": "America/Los_Angeles",
}

CSM_OTHER = {
    "csm_id": "csm_demo_002",
    "email": "jordan@nudge.local",
    "full_name": "Jordan Lee",
    "timezone": "America/New_York",
}

# Fixed edge-case account IDs (documented in EDGE_CASES.md)
EDGE_USAGE_EXPAND = "acc_edge_usage_expand"
EDGE_PAYMENT_RESOLVED = "acc_edge_payment_resolved"
EDGE_DUP_TICKETS = "acc_edge_dup_tickets"
EDGE_CRM_BILLING = "acc_edge_crm_billing"
EDGE_DISCOUNT = "acc_edge_discount"
EDGE_TOOL_OUTAGE = "acc_edge_tool_outage"
EDGE_OPT_OUT = "acc_edge_opt_out"
EDGE_OWNERSHIP = "acc_edge_ownership"

EDGE_ACCOUNT_IDS = (
    EDGE_USAGE_EXPAND,
    EDGE_PAYMENT_RESOLVED,
    EDGE_DUP_TICKETS,
    EDGE_CRM_BILLING,
    EDGE_DISCOUNT,
    EDGE_TOOL_OUTAGE,
    EDGE_OPT_OUT,
    EDGE_OWNERSHIP,
)

INDUSTRIES = (
    "SaaS",
    "FinTech",
    "HealthTech",
    "EdTech",
    "Retail",
    "DevTools",
    "Logistics",
    "Media",
)

PLAN_TIERS = ("Starter", "Growth", "Pro", "Enterprise")

FEATURES = (
    "dashboard",
    "reports",
    "api_access",
    "sso",
    "integrations",
    "workflows",
    "ai_assist",
    "audit_log",
    "webhooks",
    "custom_fields",
    "collaboration",
    "exports",
)

COMPANY_PREFIXES = (
    "Acme",
    "Bright",
    "North",
    "Summit",
    "Cascade",
    "Orbit",
    "Lumen",
    "Vertex",
    "Harbor",
    "Pine",
    "Cedar",
    "Atlas",
    "Nova",
    "Pulse",
    "Forge",
)

COMPANY_SUFFIXES = (
    "Analytics",
    "Labs",
    "Systems",
    "Digital",
    "Health",
    "Retail",
    "Cloud",
    "Works",
    "Group",
    "Partners",
)

DEFAULT_SEED = 42
DEFAULT_N_ACCOUNTS = 120
DEFAULT_USAGE_DAYS = 90
