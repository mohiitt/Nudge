"""Generate Nudge seed CSVs (RavenStack + synthetic CRM/billing/support/interventions)."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Allow `python data/generator/generate.py` from repo root
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from data.generator.constants import (  # noqa: E402
    COMPANY_PREFIXES,
    COMPANY_SUFFIXES,
    CSM_DEMO,
    CSM_OTHER,
    DEFAULT_N_ACCOUNTS,
    DEFAULT_SEED,
    DEFAULT_USAGE_DAYS,
    EDGE_ACCOUNT_IDS,
    EDGE_CRM_BILLING,
    EDGE_DISCOUNT,
    EDGE_DUP_TICKETS,
    EDGE_OPT_OUT,
    EDGE_OWNERSHIP,
    EDGE_PAYMENT_RESOLVED,
    EDGE_TOOL_OUTAGE,
    EDGE_USAGE_EXPAND,
    FEATURES,
    FIXTURES_DIR,
    INDUSTRIES,
    OUTPUT_DIR,
    PLAN_TIERS,
)
from data.generator.ravenstack import load_or_create_ravenstack  # noqa: E402


def _uid(prefix: str, i: int) -> str:
    return f"{prefix}_{i:05d}"


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _company_name(rng: random.Random, i: int) -> str:
    return f"{rng.choice(COMPANY_PREFIXES)}{rng.choice(COMPANY_SUFFIXES)} {i}"


def build_edge_accounts(today: date) -> list[dict]:
    demo = CSM_DEMO["csm_id"]
    other = CSM_OTHER["csm_id"]
    specs = [
        (EDGE_USAGE_EXPAND, "Expanding Ops Co", "expansion", demo, 180000, today + timedelta(days=120)),
        (EDGE_PAYMENT_RESOLVED, "PaidLate Systems", "active", demo, 64000, today + timedelta(days=60)),
        (EDGE_DUP_TICKETS, "DupTicket Labs", "churn_risk", demo, 52000, today + timedelta(days=40)),
        (EDGE_CRM_BILLING, "Conflict CRM Inc", "active", demo, 99000, today + timedelta(days=75)),
        (EDGE_DISCOUNT, "Discount Seekers", "churn_risk", demo, 41000, today + timedelta(days=20)),
        (EDGE_TOOL_OUTAGE, "Outage Probe LLC", "active", demo, 33000, today + timedelta(days=100)),
        (EDGE_OPT_OUT, "Quiet Marketing Co", "active", demo, 28000, today + timedelta(days=150)),
        (EDGE_OWNERSHIP, "Other Owner Corp", "active", other, 77000, today + timedelta(days=55)),
    ]
    rows = []
    for aid, name, status, owner, arr, renewal in specs:
        rows.append(
            {
                "account_id": aid,
                "name": name,
                "industry": "SaaS",
                "arr": arr,
                "plan_tier": "Growth",
                "renewal_date": renewal.isoformat(),
                "health_score": 0.5,
                "status": status,
                "owner_csm_id": owner,
                "marketing_opt_out": 1 if aid == EDGE_OPT_OUT else 0,
                "created_at": datetime.utcnow().isoformat(timespec="seconds"),
            }
        )
    return rows


def generate(
    n_accounts: int = DEFAULT_N_ACCOUNTS,
    usage_days: int = DEFAULT_USAGE_DAYS,
    seed: int = DEFAULT_SEED,
    out_dir: Path = OUTPUT_DIR,
) -> Path:
    rng = random.Random(seed)
    today = date.today()
    raven_path = load_or_create_ravenstack(n=n_accounts, seed=seed)

    csms = [CSM_DEMO, CSM_OTHER]
    accounts: list[dict] = []
    ownership: list[dict] = []
    subscriptions: list[dict] = []
    invoices: list[dict] = []
    usage: list[dict] = []
    features: list[dict] = []
    tickets: list[dict] = []
    comments: list[dict] = []
    activities: list[dict] = []
    interventions: list[dict] = []

    # Baseline from RavenStack rows + synthetic fill
    with raven_path.open(encoding="utf-8") as fh:
        raven_rows = list(csv.DictReader(fh))[: max(0, n_accounts - len(EDGE_ACCOUNT_IDS))]

    for i, rr in enumerate(raven_rows):
        aid = f"acc_{i:04d}"
        owner = CSM_DEMO["csm_id"] if i % 7 else CSM_OTHER["csm_id"]
        if i < 80:
            owner = CSM_DEMO["csm_id"]
        mrr = float(rr.get("mrr") or rng.uniform(200, 20000))
        arr = round(mrr * 12, 2)
        status = "churned" if str(rr.get("churned")) in {"1", "true", "True"} else "active"
        if status == "active" and rng.random() < 0.12:
            status = "churn_risk"
        renewal = today + timedelta(days=rng.randint(14, 200))
        accounts.append(
            {
                "account_id": aid,
                "name": rr.get("company_name") or _company_name(rng, i),
                "industry": rr.get("industry") or rng.choice(INDUSTRIES),
                "arr": arr,
                "plan_tier": rr.get("plan") or rng.choice(PLAN_TIERS),
                "renewal_date": renewal.isoformat(),
                "health_score": round(rng.uniform(0.3, 0.95), 2),
                "status": status,
                "owner_csm_id": owner,
                "marketing_opt_out": 0,
                "created_at": datetime.utcnow().isoformat(timespec="seconds"),
            }
        )

    accounts.extend(build_edge_accounts(today))

    for a in accounts:
        aid = a["account_id"]
        owner = a["owner_csm_id"]
        ownership.append(
            {
                "account_id": aid,
                "owner_csm_id": owner,
                "effective_from": (today - timedelta(days=365)).isoformat(),
                "effective_to": "",
            }
        )
        mrr = round(float(a["arr"]) / 12, 2)
        seats = rng.randint(5, 200)
        # Edge: expanding seats despite usage decline
        if aid == EDGE_USAGE_EXPAND:
            seats = 180
            mrr = round(mrr * 1.25, 2)
        # Edge: CRM vs billing conflict — subscription MRR much lower than account ARR
        sub_mrr = 1200.0 if aid == EDGE_CRM_BILLING else mrr
        subscriptions.append(
            {
                "subscription_id": f"sub_{aid}",
                "account_id": aid,
                "stripe_sub_id": f"sub_test_{aid}",
                "plan_name": a["plan_tier"],
                "mrr": sub_mrr,
                "seats": seats,
                "status": "active",
                "started_at": (today - timedelta(days=200)).isoformat(),
                "ends_at": a["renewal_date"],
            }
        )

        # Invoices
        for j in range(3):
            inv_status = "paid"
            paid_at = (today - timedelta(days=30 * (3 - j))).isoformat()
            failure = ""
            if aid == EDGE_PAYMENT_RESOLVED and j == 1:
                inv_status = "paid"
                failure = "card_declined_then_resolved"
            elif aid == EDGE_PAYMENT_RESOLVED and j == 0:
                # historical failed then later paid duplicate pattern
                invoices.append(
                    {
                        "invoice_id": f"inv_{aid}_{j}_fail",
                        "account_id": aid,
                        "stripe_invoice_id": f"in_fail_{aid}",
                        "amount": mrr,
                        "currency": "USD",
                        "status": "failed",
                        "due_date": (today - timedelta(days=45)).isoformat(),
                        "paid_at": "",
                        "failure_reason": "card_declined",
                        "created_at": (today - timedelta(days=45)).isoformat(),
                    }
                )
            invoices.append(
                {
                    "invoice_id": f"inv_{aid}_{j}",
                    "account_id": aid,
                    "stripe_invoice_id": f"in_{aid}_{j}",
                    "amount": mrr,
                    "currency": "USD",
                    "status": inv_status,
                    "due_date": (today - timedelta(days=30 * (3 - j))).isoformat(),
                    "paid_at": paid_at,
                    "failure_reason": failure,
                    "created_at": (today - timedelta(days=30 * (3 - j))).isoformat(),
                }
            )

        # Usage daily
        for d in range(usage_days):
            day = today - timedelta(days=usage_days - d)
            base = rng.randint(20, 200)
            # Decline in last 30d for usage_expand edge
            if aid == EDGE_USAGE_EXPAND and d >= usage_days - 30:
                base = int(base * 0.45)
            elif aid == EDGE_USAGE_EXPAND:
                base = int(base * 1.2)
            usage.append(
                {
                    "account_id": aid,
                    "usage_date": day.isoformat(),
                    "dau": max(1, base // 3),
                    "sessions": base,
                    "events": base * rng.randint(3, 8),
                    "feature_events": base,
                }
            )

        for feat in rng.sample(list(FEATURES), k=min(5, len(FEATURES))):
            features.append(
                {
                    "account_id": aid,
                    "feature_name": feat,
                    "first_used_at": (today - timedelta(days=90)).isoformat(),
                    "last_used_at": (today - timedelta(days=rng.randint(0, 20))).isoformat(),
                    "use_count_30d": rng.randint(0, 400),
                    "adoption_pct": round(rng.uniform(0.05, 0.95), 2),
                }
            )

        # Tickets
        n_tickets = 2 if aid != EDGE_DUP_TICKETS else 3
        for t in range(n_tickets):
            tid = f"tkt_{aid}_{t}"
            subject = "SSO login failures" if aid == EDGE_DUP_TICKETS else rng.choice(
                ["Billing question", "Feature request", "Performance", "Onboarding help"]
            )
            tickets.append(
                {
                    "ticket_id": tid,
                    "account_id": aid,
                    "owner_csm_id": owner,
                    "subject": subject,
                    "description": f"Conversation about {subject.lower()} for {a['name']}",
                    "status": "open" if t == 0 else "pending",
                    "priority": "high" if aid == EDGE_DUP_TICKETS else "normal",
                    "category": "auth" if aid == EDGE_DUP_TICKETS else "general",
                    "sentiment": "negative" if t == 0 else "neutral",
                    "created_at": (datetime.utcnow() - timedelta(days=5 + t)).isoformat(timespec="seconds"),
                    "updated_at": datetime.utcnow().isoformat(timespec="seconds"),
                    "resolved_at": "",
                }
            )
            comments.append(
                {
                    "comment_id": f"cmt_{tid}_0",
                    "ticket_id": tid,
                    "author_type": "end_user",
                    "body": f"We keep hitting issues: {subject}. Contact jane.doe@example.com",
                    "created_at": datetime.utcnow().isoformat(timespec="seconds"),
                }
            )

        activities.append(
            {
                "activity_id": f"act_{aid}_0",
                "account_id": aid,
                "owner_csm_id": owner,
                "activity_type": "note",
                "subject": "QBR prep",
                "body": f"Notes for {a['name']}"
                + (" ARR in CRM overstated vs Stripe" if aid == EDGE_CRM_BILLING else ""),
                "hubspot_id": f"hs_{aid}",
                "occurred_at": (datetime.utcnow() - timedelta(days=3)).isoformat(timespec="seconds"),
                "created_at": datetime.utcnow().isoformat(timespec="seconds"),
            }
        )

        interventions.append(
            {
                "intervention_id": f"int_{aid}_0",
                "account_id": aid,
                "owner_csm_id": owner,
                "action_type": "external_email",
                "summary": f"Check-in outreach for {a['name']}",
                "plan_json": json.dumps({"steps": ["draft_email", "create_task"]}),
                "outcome": "improved" if rng.random() < 0.4 else "pending",
                "outcome_measured_at": "",
                "created_at": (datetime.utcnow() - timedelta(days=14)).isoformat(timespec="seconds"),
                "edge_tag": (
                    "discount_seed"
                    if aid == EDGE_DISCOUNT
                    else "tool_outage_seed"
                    if aid == EDGE_TOOL_OUTAGE
                    else ""
                ),
            }
        )

    # CSVs
    _write_csv(out_dir / "csms.csv", csms)
    _write_csv(out_dir / "accounts.csv", accounts)
    _write_csv(out_dir / "account_ownership.csv", ownership)
    _write_csv(out_dir / "subscriptions.csv", subscriptions)
    _write_csv(out_dir / "invoices_payments.csv", invoices)
    _write_csv(out_dir / "usage_daily.csv", usage)
    _write_csv(out_dir / "feature_adoption.csv", features)
    _write_csv(out_dir / "support_tickets.csv", tickets)
    _write_csv(out_dir / "ticket_comments.csv", comments)
    _write_csv(out_dir / "crm_activities.csv", activities)
    _write_csv(out_dir / "interventions.csv", interventions)

    # Small fixtures for demos / web
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    demo_accounts = [a for a in accounts if a["owner_csm_id"] == CSM_DEMO["csm_id"]][:5]
    edge = [a for a in accounts if a["account_id"] in EDGE_ACCOUNT_IDS]
    _write_csv(FIXTURES_DIR / "accounts_sample.csv", demo_accounts + edge)
    (FIXTURES_DIR / "meta.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "n_accounts": len(accounts),
                "edge_cases": list(EDGE_ACCOUNT_IDS),
                "ravenstack_source": str(raven_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(accounts)} accounts → {out_dir}")
    return out_dir


def main() -> None:
    p = argparse.ArgumentParser(description="Generate Nudge synthetic datasets")
    p.add_argument("--accounts", type=int, default=DEFAULT_N_ACCOUNTS)
    p.add_argument("--usage-days", type=int, default=DEFAULT_USAGE_DAYS)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--out", type=Path, default=OUTPUT_DIR)
    args = p.parse_args()
    generate(n_accounts=args.accounts, usage_days=args.usage_days, seed=args.seed, out_dir=args.out)


if __name__ == "__main__":
    main()
