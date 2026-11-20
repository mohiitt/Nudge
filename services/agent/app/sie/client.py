"""SIE (Superlinked Serverless) client.

Base URL: https://api.superlinked.com (SIE_BASE_URL).
Endpoint paths are best-effort REST shapes; mocks always work without a key.

Models:
  embed    Qwen/Qwen3-Embedding-4B
  rerank   Qwen/Qwen3-Reranker-4B
  classify knowledgator/gliclass-large-v3.0
  extract  fastino/gliner2-large-v1
  redact   numind/NuNER_Zero
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from app.config import get_settings
from app.sie import cache
from app.sie.mocks import (
    EMBED_DIM,
    fake_classify,
    fake_embedding,
    fake_extract,
    fake_redact,
    fake_rerank,
)


def _use_mock() -> bool:
    s = get_settings()
    return s.mock_mode or not s.sie_api_key


def _headers() -> dict[str, str]:
    s = get_settings()
    return {
        "Authorization": f"Bearer {s.sie_api_key}",
        "Content-Type": "application/json",
    }


def _fit_dim(vec: list[float], dim: int = EMBED_DIM) -> list[float]:
    if len(vec) == dim:
        return vec
    if len(vec) > dim:
        return vec[:dim]
    return vec + [0.0] * (dim - len(vec))


class SIEClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def encode(self, text: str, *, model: Optional[str] = None) -> list[float]:
        model = model or self.settings.sie_embed_model
        cached = cache.get(text, model)
        if cached is not None:
            return cached
        if _use_mock():
            vec = fake_embedding(text)
            cache.put(text, model, vec)
            return vec
        with httpx.Client(base_url=self.settings.sie_base_url, timeout=60.0) as client:
            r = client.post(
                "/v1/embeddings",
                headers=_headers(),
                json={"model": model, "input": text},
            )
            r.raise_for_status()
            data = r.json()
            raw = data.get("data", [{}])[0].get("embedding") or data.get("embedding") or []
            vec = _fit_dim([float(x) for x in raw])
            cache.put(text, model, vec)
            return vec

    def score(self, query: str, documents: list[str], *, model: Optional[str] = None) -> list[dict[str, Any]]:
        model = model or self.settings.sie_rerank_model
        if _use_mock():
            return fake_rerank(query, documents)
        with httpx.Client(base_url=self.settings.sie_base_url, timeout=60.0) as client:
            r = client.post(
                "/v1/rerank",
                headers=_headers(),
                json={"model": model, "query": query, "documents": documents},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("results") or data.get("data") or []

    def classify(self, text: str, labels: list[str], *, model: Optional[str] = None) -> list[dict[str, Any]]:
        model = model or self.settings.sie_classify_model
        if _use_mock():
            return fake_classify(text, labels)
        with httpx.Client(base_url=self.settings.sie_base_url, timeout=60.0) as client:
            r = client.post(
                "/v1/classify",
                headers=_headers(),
                json={"model": model, "text": text, "labels": labels},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("labels") or data.get("results") or []

    def extract(self, text: str, entity_types: Optional[list[str]] = None, *, model: Optional[str] = None) -> list[dict[str, Any]]:
        model = model or self.settings.sie_extract_model
        if _use_mock():
            return fake_extract(text, entity_types)
        with httpx.Client(base_url=self.settings.sie_base_url, timeout=60.0) as client:
            r = client.post(
                "/v1/extract",
                headers=_headers(),
                json={"model": model, "text": text, "labels": entity_types or []},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("entities") or data.get("results") or []

    def redact(self, text: str, *, model: Optional[str] = None) -> str:
        model = model or self.settings.sie_redact_model
        if _use_mock():
            return fake_redact(text)
        with httpx.Client(base_url=self.settings.sie_base_url, timeout=60.0) as client:
            r = client.post(
                "/v1/redact",
                headers=_headers(),
                json={"model": model, "text": text},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("text") or data.get("redacted") or fake_redact(text)


def get_client() -> SIEClient:
    return SIEClient()
