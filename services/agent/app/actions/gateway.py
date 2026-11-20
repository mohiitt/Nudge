"""Action Gateway — env-configurable base URLs for Firedrill redirect.

Never sends real external email; drafts only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import httpx

from app.config import get_settings


class ActionGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    def create_hubspot_task(
        self,
        *,
        account_id: str,
        title: str,
        body: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> dict[str, Any]:
        s = self.settings
        payload = {
            "properties": {
                "hs_task_subject": title,
                "hs_task_body": body or "",
                "hs_timestamp": due_date or datetime.now(timezone.utc).isoformat(),
                "account_id": account_id,
            }
        }
        if not s.hubspot_access_token or s.mock_mode:
            return {"id": f"hs_task_mock_{uuid4().hex[:8]}", "mock": True, **payload}
        with httpx.Client(base_url=s.hubspot_base_url, timeout=30.0) as client:
            r = client.post(
                "/crm/v3/objects/tasks",
                headers={
                    "Authorization": f"Bearer {s.hubspot_access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    def draft_gmail(
        self,
        *,
        to: str,
        subject: str,
        body: str,
    ) -> dict[str, Any]:
        """Create a draft only — never send."""
        s = self.settings
        draft = {
            "id": f"draft_{uuid4().hex[:10]}",
            "to": to,
            "subject": subject,
            "body": body,
            "status": "draft",
            "sent": False,
        }
        if s.mock_mode:
            return {**draft, "mock": True, "base_url": s.gmail_base_url}
        # Even with credentials we only create drafts via Gmail API draft endpoint.
        # Firedrill can redirect GMAIL_BASE_URL.
        with httpx.Client(base_url=s.gmail_base_url, timeout=30.0) as client:
            try:
                r = client.post("/gmail/v1/users/me/drafts", json={"message": draft})
                if r.status_code < 400:
                    return {**draft, "provider": r.json()}
            except httpx.HTTPError:
                pass
        return draft

    def post_slack(self, *, channel: str, text: str) -> dict[str, Any]:
        s = self.settings
        payload = {"channel": channel, "text": text}
        if not s.slack_bot_token or s.mock_mode:
            return {"ok": True, "mock": True, "ts": str(uuid4()), **payload}
        with httpx.Client(base_url=s.slack_base_url, timeout=30.0) as client:
            r = client.post(
                "/chat.postMessage",
                headers={"Authorization": f"Bearer {s.slack_bot_token}"},
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    def stripe_get_customer(self, customer_id: str) -> dict[str, Any]:
        s = self.settings
        if not s.stripe_secret_key or s.mock_mode:
            return {"id": customer_id, "mock": True}
        with httpx.Client(base_url=s.stripe_base_url, auth=(s.stripe_secret_key, ""), timeout=30.0) as client:
            r = client.get(f"/v1/customers/{customer_id}")
            r.raise_for_status()
            return r.json()


def get_gateway() -> ActionGateway:
    return ActionGateway()
