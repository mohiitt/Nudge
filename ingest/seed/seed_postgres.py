"""Load accounts + Zendesk-shaped tickets into local Postgres."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "data" / "output"


def conninfo() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"user={os.getenv('POSTGRES_USER', 'nudge')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'nudge')} "
        f"dbname={os.getenv('POSTGRES_DB', 'nudge_support')}"
    )


def _read(name: str) -> list[dict]:
    path = OUTPUT / name
    if not path.exists():
        print(f"Missing {path}; run: python -m data.generator")
        sys.exit(1)
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    accounts = _read("accounts.csv")
    tickets = _read("support_tickets.csv")
    comments = _read("ticket_comments.csv") if (OUTPUT / "ticket_comments.csv").exists() else []

    with psycopg.connect(conninfo()) as conn:
        with conn.cursor() as cur:
            for a in accounts:
                cur.execute(
                    """
                    INSERT INTO accounts (account_id, name, industry, arr, plan_tier, renewal_date, status, owner_csm_id)
                    VALUES (%(account_id)s, %(name)s, %(industry)s, %(arr)s, %(plan_tier)s, %(renewal_date)s, %(status)s, %(owner_csm_id)s)
                    ON CONFLICT (account_id) DO UPDATE SET
                      name=EXCLUDED.name, arr=EXCLUDED.arr, status=EXCLUDED.status, owner_csm_id=EXCLUDED.owner_csm_id,
                      updated_at=NOW()
                    """,
                    a,
                )
            for t in tickets:
                cur.execute(
                    """
                    INSERT INTO support_tickets (
                      ticket_id, account_id, owner_csm_id, subject, description, status, priority, category, sentiment, created_at, updated_at
                    ) VALUES (
                      %(ticket_id)s, %(account_id)s, %(owner_csm_id)s, %(subject)s, %(description)s, %(status)s,
                      %(priority)s, %(category)s, %(sentiment)s, %(created_at)s::timestamptz, %(updated_at)s::timestamptz
                    )
                    ON CONFLICT (ticket_id) DO UPDATE SET status=EXCLUDED.status, updated_at=NOW()
                    """,
                    t,
                )
            for c in comments:
                cur.execute(
                    """
                    INSERT INTO ticket_comments (comment_id, ticket_id, author_type, body, created_at)
                    VALUES (%(comment_id)s, %(ticket_id)s, %(author_type)s, %(body)s, %(created_at)s::timestamptz)
                    ON CONFLICT (comment_id) DO NOTHING
                    """,
                    c,
                )
        conn.commit()
    print(f"Seeded Postgres: {len(accounts)} accounts, {len(tickets)} tickets")


if __name__ == "__main__":
    main()
