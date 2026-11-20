"""SingleStore connection helper. Returns None in MOCK_MODE / missing host."""

from __future__ import annotations

from typing import Any, Optional

from app.config import get_settings


def get_connection() -> Any | None:
    settings = get_settings()
    if settings.mock_mode or not settings.singlestore_host:
        return None
    import pymysql

    return pymysql.connect(
        host=settings.singlestore_host,
        port=settings.singlestore_port,
        user=settings.singlestore_user,
        password=settings.singlestore_password,
        database=settings.singlestore_database,
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": True},
        autocommit=True,
    )


def fetch_all(sql: str, params: Optional[dict | tuple] = None) -> list[dict]:
    conn = get_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())
    finally:
        conn.close()


def execute(sql: str, params: Optional[dict | tuple] = None) -> int:
    conn = get_connection()
    if conn is None:
        return 0
    try:
        with conn.cursor() as cur:
            n = cur.execute(sql, params or ())
            return int(n or 0)
    finally:
        conn.close()
