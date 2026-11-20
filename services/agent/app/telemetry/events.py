"""Typed helpers matching docs/events.md."""

from __future__ import annotations

from typing import Any, Optional

from app.telemetry.amplitude import get_amplitude


def agent_session_started(csm_id: str, session_id: str, source: str = "web") -> None:
    get_amplitude().track(
        "agent.session_started",
        user_id=csm_id,
        event_properties={"session_id": session_id, "source": source},
    )


def agent_tool_called(csm_id: str, tool_name: str, account_id: Optional[str] = None, latency_ms: int = 0) -> None:
    get_amplitude().track(
        "agent.tool_called",
        user_id=csm_id,
        event_properties={"tool_name": tool_name, "account_id": account_id, "latency_ms": latency_ms},
    )


def approval_requested(csm_id: str, approval_id: str, action_type: str, account_id: Optional[str] = None) -> None:
    get_amplitude().track(
        "approval.requested",
        user_id=csm_id,
        event_properties={"approval_id": approval_id, "action_type": action_type, "account_id": account_id},
    )


def approval_decided(csm_id: str, approval_id: str, decision: str, action_type: str) -> None:
    get_amplitude().track(
        "approval.decided",
        user_id=csm_id,
        event_properties={"approval_id": approval_id, "decision": decision, "action_type": action_type},
    )


def intervention_outcome_measured(
    csm_id: str,
    intervention_id: str,
    outcome: str,
    days_since: int,
) -> None:
    get_amplitude().track(
        "intervention.outcome_measured",
        user_id=csm_id,
        event_properties={
            "intervention_id": intervention_id,
            "outcome": outcome,
            "days_since": days_since,
        },
    )


def track(event_type: str, csm_id: str, props: Optional[dict[str, Any]] = None) -> None:
    get_amplitude().track(event_type, user_id=csm_id, event_properties=props or {})
