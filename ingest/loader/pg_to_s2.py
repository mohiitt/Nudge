"""Incremental Postgres → SingleStore loader (Airbyte fallback path).

Keyed on `_airbyte_extracted_at` when present, else `updated_at`.
Dry-runs when SINGLESTORE_HOST is missing or MOCK_MODE=true.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import psycopg

TABLES = ("accounts", "support_tickets")


def pg_conn():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "nudge"),
        password=os.getenv("POSTGRES_PASSWORD", "nudge"),
        dbname=os.getenv("POSTGRES_DB", "nudge_support"),
    )


def s2_conn():
    host = os.getenv("SINGLESTORE_HOST", "")
    if not host or os.getenv("MOCK_MODE", "true").lower() in {"1", "true", "yes"}:
        return None
    import pymysql

    return pymysql.connect(
        host=host,
        port=int(os.getenv("SINGLESTORE_PORT", "3306")),
        user=os.getenv("SINGLESTORE_USER", ""),
        password=os.getenv("SINGLESTORE_PASSWORD", ""),
        database=os.getenv("SINGLESTORE_DATABASE", "nudge"),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": True},
    )


def fetch_incremental(cur, table: str, since: str | None) -> list[dict]:
    # Prefer airbyte raw schema if present
    for candidate in (f"airbyte_raw.{table}", table):
        try:
            if since:
                cur.execute(
                    f"""
                    SELECT * FROM {candidate}
                    WHERE COALESCE(_airbyte_extracted_at, updated_at, created_at) > %s
                    ORDER BY COALESCE(_airbyte_extracted_at, updated_at, created_at)
                    """,
                    (since,),
                )
            else:
                cur.execute(f"SELECT * FROM {candidate} LIMIT 10000")
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            continue
    return []


def main() -> None:
    since = os.getenv("LOADER_SINCE")  # ISO timestamp optional
    s2 = s2_conn()
    with pg_conn() as pg:
        with pg.cursor() as cur:
            for table in TABLES:
                rows = fetch_incremental(cur, table, since)
                print(f"{table}: {len(rows)} rows since {since or 'beginning'}")
                if s2 is None:
                    print(f"  [dry-run] would upsert into SingleStore.{table}")
                    continue
                # Minimal upsert for accounts / tickets
                with s2.cursor() as sc:
                    for row in rows:
                        if table == "accounts":
                            sc.execute(
                                """
                                INSERT INTO accounts (account_id, name, industry, arr, plan_tier, renewal_date, status, owner_csm_id)
                                VALUES (%(account_id)s, %(name)s, %(industry)s, %(arr)s, %(plan_tier)s, %(renewal_date)s, %(status)s, %(owner_csm_id)s)
                                ON DUPLICATE KEY UPDATE name=VALUES(name), arr=VALUES(arr), status=VALUES(status), owner_csm_id=VALUES(owner_csm_id)
                                """,
                                row,
                            )
                        elif table == "support_tickets":
                            sc.execute(
                                """
                                INSERT INTO support_tickets (
                                  ticket_id, account_id, owner_csm_id, subject, status, priority, category, sentiment, created_at, updated_at
                                ) VALUES (
                                  %(ticket_id)s, %(account_id)s, %(owner_csm_id)s, %(subject)s, %(status)s, %(priority)s,
                                  %(category)s, %(sentiment)s, %(created_at)s, %(updated_at)s
                                )
                                ON DUPLICATE KEY UPDATE status=VALUES(status), updated_at=VALUES(updated_at)
                                """,
                                row,
                            )
                s2.commit()
    if s2:
        s2.close()
    print(f"Done at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
