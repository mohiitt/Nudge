"""Amplitude HTTP V2 client — Free plan max 10 events per request."""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from app.config import get_settings

BATCH_LIMIT = 10


class AmplitudeClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._queue: list[dict[str, Any]] = []

    def track(
        self,
        event_type: str,
        *,
        user_id: Optional[str] = None,
        event_properties: Optional[dict[str, Any]] = None,
        device_id: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> None:
        event: dict[str, Any] = {
            "event_type": event_type,
            "time": int(time.time() * 1000),
            "event_properties": event_properties or {},
        }
        if user_id:
            event["user_id"] = user_id
        if device_id:
            event["device_id"] = device_id
        if session_id is not None:
            event["session_id"] = session_id
        if not user_id and not device_id:
            event["device_id"] = "nudge-server"
        self._queue.append(event)
        if len(self._queue) >= BATCH_LIMIT:
            self.flush()

    def flush(self) -> dict[str, Any]:
        if not self._queue:
            return {"code": 200, "events_ingested": 0}
        s = self.settings
        if s.mock_mode or not s.amplitude_api_key:
            n = len(self._queue)
            self._queue.clear()
            return {"code": 200, "events_ingested": n, "mock": True}

        ingested = 0
        with httpx.Client(timeout=15.0) as client:
            while self._queue:
                batch = self._queue[:BATCH_LIMIT]
                del self._queue[:BATCH_LIMIT]
                r = client.post(
                    s.amplitude_api_url,
                    json={"api_key": s.amplitude_api_key, "events": batch},
                )
                r.raise_for_status()
                ingested += len(batch)
        return {"code": 200, "events_ingested": ingested}


_client: AmplitudeClient | None = None


def get_amplitude() -> AmplitudeClient:
    global _client
    if _client is None:
        _client = AmplitudeClient()
    return _client
