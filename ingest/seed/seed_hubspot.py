"""Seed HubSpot companies/notes, or write fixtures when no token."""

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
    token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
    base = os.getenv("HUBSPOT_BASE_URL", "https://api.hubapi.com").rstrip("/")
    accounts_path = OUTPUT / "accounts.csv"
    accounts = list(csv.DictReader(accounts_path.open()))[:10] if accounts_path.exists() else []

    if not token:
        payload = {
            "mode": "fixture",
            "companies": [
                {"properties": {"name": a["name"], "account_id": a["account_id"]}} for a in accounts
            ],
        }
        (FIXTURES / "hubspot_companies.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("No HUBSPOT_ACCESS_TOKEN — wrote ingest/seed/fixtures/hubspot_companies.json")
        return

    created = []
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(base_url=base, headers=headers, timeout=30.0) as client:
        for a in accounts:
            r = client.post(
                "/crm/v3/objects/companies",
                json={"properties": {"name": a["name"], "description": a["account_id"]}},
            )
            r.raise_for_status()
            created.append(r.json())
    (FIXTURES / "hubspot_companies.json").write_text(json.dumps({"mode": "live", "companies": created}, indent=2), encoding="utf-8")
    print(f"Created {len(created)} HubSpot companies")


if __name__ == "__main__":
    main()
