"""Embedding cache: SingleStore embedding_cache when available, else memory."""

from __future__ import annotations

import hashlib
from typing import Optional

from app.data import db
from app.sie.mocks import EMBED_DIM

_MEM: dict[str, list[float]] = {}


def content_hash(text: str, model: str) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode("utf-8")).hexdigest()


def get(text: str, model: str) -> Optional[list[float]]:
    key = content_hash(text, model)
    if key in _MEM:
        return _MEM[key]
    rows = db.fetch_all(
        "SELECT embedding FROM embedding_cache WHERE content_hash=%(h)s AND model=%(m)s LIMIT 1",
        {"h": key, "m": model},
    )
    if not rows:
        return None
    emb = rows[0]["embedding"]
    if isinstance(emb, (bytes, bytearray)):
        return None  # unexpected binary; skip
    if isinstance(emb, str):
        # SingleStore may return vector as string "[...]"
        try:
            vals = [float(x) for x in emb.strip("[]").split(",") if x.strip()]
            _MEM[key] = vals
            return vals
        except ValueError:
            return None
    if isinstance(emb, list):
        _MEM[key] = emb
        return emb
    return None


def put(text: str, model: str, embedding: list[float]) -> None:
    key = content_hash(text, model)
    vec = embedding[:EMBED_DIM] + [0.0] * max(0, EMBED_DIM - len(embedding))
    _MEM[key] = vec
    db.execute(
        """
        INSERT INTO embedding_cache (content_hash, model, embedding)
        VALUES (%(h)s, %(m)s, %(e)s)
        ON DUPLICATE KEY UPDATE embedding=VALUES(embedding)
        """,
        {"h": key, "m": model, "e": str(vec)},
    )
