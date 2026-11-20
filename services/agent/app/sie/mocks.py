"""Deterministic fake SIE responses when API key missing / MOCK_MODE."""

from __future__ import annotations

import hashlib
import math
from typing import Any


EMBED_DIM = 2560


def fake_embedding(text: str, dim: int = EMBED_DIM) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals: list[float] = []
    seed = int.from_bytes(digest[:8], "big")
    for i in range(dim):
        # simple LCG-ish expansion
        seed = (seed * 6364136223846793005 + i) & 0xFFFFFFFFFFFFFFFF
        vals.append(((seed % 10000) / 5000.0) - 1.0)
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / norm for v in vals]


def fake_rerank(query: str, documents: list[str]) -> list[dict[str, Any]]:
    q = fake_embedding(query)
    scored = []
    for i, doc in enumerate(documents):
        d = fake_embedding(doc)
        score = sum(a * b for a, b in zip(q, d))
        scored.append({"index": i, "document": doc, "score": score})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def fake_classify(text: str, labels: list[str]) -> list[dict[str, Any]]:
    emb = fake_embedding(text)
    out = []
    for label in labels:
        score = abs(sum(a * b for a, b in zip(emb, fake_embedding(label))))
        out.append({"label": label, "score": min(1.0, score)})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def fake_extract(text: str, entity_types: list[str] | None = None) -> list[dict[str, Any]]:
    # trivial token extract
    entities = []
    for token in text.replace(",", " ").split():
        if "@" in token or token[:1].isupper():
            entities.append({"text": token, "label": (entity_types or ["ENTITY"])[0]})
    return entities[:20]


def fake_redact(text: str) -> str:
    import re

    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)
    return text
