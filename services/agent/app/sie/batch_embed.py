"""Batch embed ticket/playbook/intervention texts with cache skips."""

from __future__ import annotations

from typing import Iterable

from app.sie.client import get_client


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    client = get_client()
    out: list[list[float]] = []
    cache_hits = 0
    embedded = 0
    for text in texts:
        before = len(out)
        vec = client.encode(text)
        out.append(vec)
        # cache.get is used inside encode; count heuristically
        embedded += 1
        _ = before
    print(f"batch_embed: processed={embedded} (cache handled inside encode)")
    return out


def embed_ticket_rows(rows: list[dict]) -> list[dict]:
    client = get_client()
    for row in rows:
        text = row.get("text_redacted") or row.get("body") or ""
        row["embedding"] = client.encode(client.redact(text) if text else "")
    return rows


if __name__ == "__main__":
    samples = ["SSO login failures", "Billing invoice mismatch", "Expansion seats added"]
    vecs = embed_texts(samples)
    print(f"Embedded {len(vecs)} texts, dim={len(vecs[0]) if vecs else 0}")
