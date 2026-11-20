"""Claude tool definitions and dispatchers."""

from __future__ import annotations

import json
from typing import Any, Callable

from app.actions.gateway import get_gateway
from app.agent import memory as mem
from app.config import get_settings
from app.data.context import (
    find_similar_interventions,
    get_account_deep_dive,
    get_account_risk,
    get_briefing,
)
from app.data.ownership import OwnershipError, assert_owns_account
from app.policy import approvals

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_briefing",
        "description": "Daily risk briefing for the CSM's owned accounts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["csm_id"],
        },
    },
    {
        "name": "get_account_risk",
        "description": "Risk signals for one owned account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
            },
            "required": ["csm_id", "account_id"],
        },
    },
    {
        "name": "find_similar_accounts",
        "description": "Find similar owned accounts and past intervention outcomes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["csm_id", "account_id"],
        },
    },
    {
        "name": "draft_message",
        "description": "Draft an external email (creates approval; never sends).",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
                "intent": {"type": "string"},
                "tone": {"type": "string"},
                "channel": {"type": "string"},
            },
            "required": ["csm_id", "account_id", "intent"],
        },
    },
    {
        "name": "escalate",
        "description": "Escalate via Slack (may require approval).",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
                "summary": {"type": "string"},
                "urgency": {"type": "string"},
            },
            "required": ["csm_id", "account_id", "summary"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a HubSpot task for an owned account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["csm_id", "account_id", "title"],
        },
    },
    {
        "name": "memory_read",
        "description": "Read CSM agent memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
            },
            "required": ["csm_id"],
        },
    },
    {
        "name": "memory_write",
        "description": "Write CSM agent memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "content": {"type": "string"},
                "memory_type": {"type": "string"},
                "account_id": {"type": "string"},
            },
            "required": ["csm_id", "content"],
        },
    },
    {
        "name": "propose_discount",
        "description": "Propose a discount (always creates an approval; never applies).",
        "input_schema": {
            "type": "object",
            "properties": {
                "csm_id": {"type": "string"},
                "account_id": {"type": "string"},
                "reason": {"type": "string"},
                "percent": {"type": "number"},
            },
            "required": ["csm_id", "account_id"],
        },
    },
]


def _serialize(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


def _json(obj: Any) -> str:
    return json.dumps(_serialize(obj), default=str)


def run_tool(
    name: str,
    args: dict[str, Any],
    *,
    session_csm_id: str | None = None,
) -> str:
    """Dispatch a tool. When session_csm_id is set it always wins over args.csm_id."""
    if session_csm_id is not None:
        csm_id = session_csm_id
    else:
        csm_id = args.get("csm_id") or get_settings().default_csm_id
    try:
        if name == "get_briefing":
            return _json(get_briefing(csm_id, limit=int(args.get("limit") or 5)))
        if name == "get_account_risk":
            return _json(get_account_risk(csm_id, args["account_id"]))
        if name == "find_similar_accounts":
            return _json(
                find_similar_interventions(csm_id, args["account_id"], limit=int(args.get("limit") or 5))
            )
        if name == "draft_message":
            assert_owns_account(csm_id, args["account_id"])
            draft = get_gateway().draft_gmail(
                to="contact@example.com",
                subject=f"Nudge: {args.get('intent', 'check-in')[:60]}",
                body=f"Intent: {args.get('intent')}\nTone: {args.get('tone') or 'helpful'}",
            )
            apr = approvals.create_approval(
                csm_id=csm_id,
                action_type="external_email",
                title=f"Email draft for {args['account_id']}",
                description="Draft only — will not send until approved.",
                account_id=args["account_id"],
                payload=draft,
            )
            return _json({"draft": draft, "approval": apr, "status": "pending_approval"})
        if name == "escalate":
            assert_owns_account(csm_id, args["account_id"])
            if approvals.requires_approval(csm_id, "slack_escalate"):
                apr = approvals.create_approval(
                    csm_id=csm_id,
                    action_type="slack_escalate",
                    title=f"Slack escalate {args['account_id']}",
                    description=args.get("summary"),
                    account_id=args["account_id"],
                    payload={"summary": args.get("summary"), "urgency": args.get("urgency")},
                )
                return _json({"status": "pending_approval", "approval": apr})
            result = get_gateway().post_slack(channel="#cs-escalations", text=args["summary"])
            return _json({"status": "executed", "result": result})
        if name == "create_task":
            assert_owns_account(csm_id, args["account_id"])
            if approvals.requires_approval(csm_id, "create_task"):
                apr = approvals.create_approval(
                    csm_id=csm_id,
                    action_type="create_task",
                    title=args["title"],
                    account_id=args["account_id"],
                    payload=args,
                )
                return _json({"status": "pending_approval", "approval": apr})
            result = get_gateway().create_hubspot_task(
                account_id=args["account_id"],
                title=args["title"],
                body=args.get("body"),
            )
            return _json({"status": "executed", "result": result})
        if name == "memory_read":
            account_id = args.get("account_id")
            if account_id:
                assert_owns_account(csm_id, account_id)
            return _json(mem.memory_to_dicts(mem.memory_read(csm_id=csm_id, account_id=account_id)))
        if name == "memory_write":
            account_id = args.get("account_id")
            if account_id:
                assert_owns_account(csm_id, account_id)
            entry = mem.memory_write(
                csm_id=csm_id,
                content=args["content"],
                memory_type=args.get("memory_type") or "note",
                account_id=account_id,
            )
            return _json(entry)
        if name == "propose_discount":
            # Sensitive — always approval; used by Firedrill unauthorized discount scenario
            assert_owns_account(csm_id, args["account_id"])
            apr = approvals.create_approval(
                csm_id=csm_id,
                action_type="discount",
                title=f"Discount request for {args['account_id']}",
                description=args.get("reason") or "Discount proposal",
                account_id=args["account_id"],
                payload={**args, "csm_id": csm_id},
            )
            return _json({"status": "pending_approval", "approval": apr})
        return json.dumps({"error": f"unknown tool {name}"})
    except OwnershipError as exc:
        return json.dumps({"error": "ownership_boundary", "detail": str(exc), "skipped": True})
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": type(exc).__name__, "detail": str(exc)})


DISPATCH: dict[str, Callable[[dict[str, Any]], str]] = {
    t["name"]: (lambda a, n=t["name"]: run_tool(n, a)) for t in TOOL_SCHEMAS
}
