#!/usr/bin/env python3
"""Check SingleStore local_infile for Airbyte MySQL destination spike.

Uses SINGLESTORE_* env vars. With MOCK_MODE=true or missing credentials,
prints mock guidance and exits 0.
"""
from __future__ import annotations

import os
import sys


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def main() -> int:
    mock = _env("MOCK_MODE", "true").lower() in ("1", "true", "yes")
    host = _env("SINGLESTORE_HOST")
    if mock or not host:
        print("[mock] No SINGLESTORE_HOST (or MOCK_MODE=true).")
        print("[mock] Would run: SHOW GLOBAL VARIABLES LIKE 'local_infile';")
        print("[mock] Expected Value=ON before Airbyte MySQL destination sync.")
        print("[mock] Apply: ingest/spike/enable_local_infile.sql")
        return 0

    try:
        import pymysql
    except ImportError:
        print("pymysql required for live check: pip install pymysql", file=sys.stderr)
        return 1

    conn = pymysql.connect(
        host=host,
        port=int(_env("SINGLESTORE_PORT", "3306")),
        user=_env("SINGLESTORE_USER"),
        password=_env("SINGLESTORE_PASSWORD"),
        database=_env("SINGLESTORE_DATABASE", "nudge"),
        ssl={"check_hostname": False},
        connect_timeout=15,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW GLOBAL VARIABLES LIKE 'local_infile'")
            row = cur.fetchone()
            if not row:
                print("local_infile variable not found", file=sys.stderr)
                return 1
            name, value = row[0], str(row[1])
            print(f"{name}={value}")
            if value.upper() not in ("ON", "1", "TRUE"):
                print(
                    "FAIL: set with ingest/spike/enable_local_infile.sql",
                    file=sys.stderr,
                )
                return 2
            print("OK: local_infile enabled for Airbyte MySQL destination.")
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
