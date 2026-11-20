"""Claude tool-calling loop with MOCK_MODE deterministic fallback."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.agent.tools import TOOL_SCHEMAS, run_tool
from app.config import get_settings
from app.contracts import ActionRequest, Approval, ChatResponse
from app.data.context import get_briefing
from app.policy import approvals


SYSTEM = """You are Nudge, a personal Customer Success agent for one CSM.
Always respect ownership: only discuss accounts owned by the given csm_id.
Sensitive actions (email, discount, contract change, refund) require approval — never claim they were sent/executed.
Be concise and actionable."""


def _mock_loop(message: str, csm_id: str, session: Optional[str]) -> ChatResponse:
    """Deterministic tool exercise without Anthropic."""
    actions: list[ActionRequest] = []
    aprs: list[Approval] = []
    lower = message.lower()

    if "own" in lower and ("acc_edge_ownership" in lower or "other owner" in lower):
        result = run_tool(
            "get_account_risk",
            {"account_id": "acc_edge_ownership"},
            session_csm_id=csm_id,
        )
        reply = (
            "I can't access that account — ownership boundary. "
            f"Tool result: {result}"
        )
        return ChatResponse(reply=reply, session=session, actions=actions, approvals=aprs)

    if "discount" in lower:
        m = re.search(r"acc_[\w]+", message)
        account_id = m.group(0) if m else "acc_edge_discount"
        result = json.loads(
            run_tool(
                "propose_discount",
                {"account_id": account_id, "reason": message, "percent": 20},
                session_csm_id=csm_id,
            )
        )
        if "approval" in result:
            apr = Approval.model_validate(result["approval"])
            aprs.append(apr)
        reply = "Discount requires your approval before any change is made. I've filed an approval request."
        return ChatResponse(reply=reply, session=session, actions=actions, approvals=aprs)

    if "draft" in lower or "email" in lower:
        m = re.search(r"acc_[\w]+", message)
        account_id = m.group(0) if m else "acc_acme"
        result = json.loads(
            run_tool(
                "draft_message",
                {"account_id": account_id, "intent": message},
                session_csm_id=csm_id,
            )
        )
        if result.get("approval"):
            aprs.append(Approval.model_validate(result["approval"]))
        reply = "Drafted an email and queued it for approval — nothing will be sent until you approve."
        return ChatResponse(reply=reply, session=session, actions=actions, approvals=aprs)

    # Default: briefing
    briefing = get_briefing(csm_id, limit=3)
    run_tool(
        "memory_write",
        {"content": f"Asked: {message[:120]}", "memory_type": "note"},
        session_csm_id=csm_id,
    )
    lines = [briefing.summary or "Here's what needs attention:"]
    for item in briefing.items:
        lines.append(
            f"- {item.account.name} ({item.account.account_id}): risk {item.risk.risk_score:.2f} — "
            + "; ".join(item.top_reasons[:2])
        )
    lines.append("Say an account id to deep-dive, or ask me to draft an email / create a task.")
    return ChatResponse(reply="\n".join(lines), session=session, actions=actions, approvals=aprs)


def run_chat(message: str, *, csm_id: Optional[str] = None, session: Optional[str] = None) -> ChatResponse:
    settings = get_settings()
    csm_id = csm_id or settings.default_csm_id

    if settings.mock_mode or not settings.anthropic_api_key:
        return _mock_loop(message, csm_id, session)

    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages: list[dict[str, Any]] = [{"role": "user", "content": message}]
    tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in TOOL_SCHEMAS
    ]

    collected_approvals: list[Approval] = []
    for _ in range(6):
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=SYSTEM + f"\nActive csm_id={csm_id}",
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason == "tool_use":
            tool_results = []
            assistant_content = resp.content
            messages.append({"role": "assistant", "content": assistant_content})
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                args = dict(block.input or {})
                # Bind csm_id server-side — never trust LLM/tool args for identity.
                result = run_tool(block.name, args, session_csm_id=csm_id)
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict) and parsed.get("approval"):
                        collected_approvals.append(Approval.model_validate(parsed["approval"]))
                except Exception:
                    pass
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            continue

        text_parts = [b.text for b in resp.content if hasattr(b, "text")]
        reply = "\n".join(text_parts) or "Done."
        # Also surface any pending approvals for this CSM
        pending = approvals.list_approvals(csm_id=csm_id)
        pending = [a for a in pending if a.status.value == "pending"][:5]
        return ChatResponse(
            reply=reply,
            session=session,
            actions=[],
            approvals=collected_approvals or pending,
        )

    return ChatResponse(reply="I hit the tool-loop limit — try a narrower question.", session=session)
