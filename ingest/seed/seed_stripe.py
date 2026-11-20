"""Seed Stripe test mode customers/subs, or write fixtures when no key."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = REPO / "data" / "output"


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    key = os.getenv("STRIPE_SECRET_KEY", "")
    base = os.getenv("STRIPE_BASE_URL", "https://api.stripe.com").rstrip("/")
    accounts_path = OUTPUT / "accounts.csv"
    accounts = list(csv.DictReader(accounts_path.open()))[:10] if accounts_path.exists() else []

    if not key:
        payload = {
            "mode": "fixture",
            "customers": [
                {"id": f"cus_test_{a['account_id']}", "name": a["name"], "metadata": {"account_id": a["account_id"]}}
                for a in accounts
            ],
        }
        (FIXTURES / "stripe_customers.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("No STRIPE_SECRET_KEY — wrote ingest/seed/fixtures/stripe_customers.json")
        return

    created = []
    with httpx.Client(base_url=base, auth=(key, ""), timeout=30.0) as client:
        for a in accounts:
            r = client.post(
                "/v1/customers",
                data={"name": a["name"], "metadata[account_id]": a["account_id"]},
            )
            r.raise_for_status()
            created.append(r.json())
    (FIXTURES / "stripe_customers.json").write_text(json.dumps({"mode": "live", "customers": created}, indent=2), encoding="utf-8")
    print(f"Created {len(created)} Stripe test customers")


if __name__ == "__main__":
    main()
