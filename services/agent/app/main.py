"""FastAPI entrypoint — Firedrill http.v1 compatible /chat."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.actions.gateway import get_gateway
from app.agent.loop import run_chat
from app.config import get_settings
from app.contracts import (
    AccountDeepDive,
    Approval,
    ApprovalDecision,
    ChatRequest,
    ChatResponse,
    DailyBriefing,
)
from app.data.context import get_account_deep_dive, get_briefing
from app.data.ownership import OwnershipError
from app.policy import approvals

settings = get_settings()

app = FastAPI(title="Nudge Agent", version="0.1.0")
_cors_origins = [o for o in {settings.web_origin, "http://localhost:3000"} if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mock_mode": settings.mock_mode,
        "default_csm_id": settings.default_csm_id,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    """Firedrill http.v1: POST {\"message\",\"session\"} → {\"reply\"}."""
    csm_id = body.csm_id or settings.default_csm_id
    return run_chat(body.message, csm_id=csm_id, session=body.session)


@app.get("/briefing/{csm_id}", response_model=DailyBriefing)
def briefing(csm_id: str, limit: int = Query(5, ge=1, le=20)) -> DailyBriefing:
    return get_briefing(csm_id, limit=limit)


@app.get("/accounts/{account_id}", response_model=AccountDeepDive)
def account_deep_dive(
    account_id: str,
    csm_id: str = Query(default=None),
) -> AccountDeepDive:
    csm = csm_id or settings.default_csm_id
    try:
        return get_account_deep_dive(csm, account_id)
    except OwnershipError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="account not found") from exc


@app.get("/approvals", response_model=list[Approval])
def list_approvals(
    csm_id: str = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[Approval]:
    csm = csm_id or settings.default_csm_id
    st = None
    if status:
        from app.contracts import ApprovalStatus

        st = ApprovalStatus(status)
    return approvals.list_approvals(csm_id=csm, status=st)


class DecideBody(BaseModel):
    decision: str
    decided_by: Optional[str] = None
    note: Optional[str] = None
    csm_id: Optional[str] = None


@app.post("/approvals/{approval_id}/decide", response_model=Approval)
def decide(approval_id: str, body: DecideBody) -> Approval:
    csm = body.csm_id or body.decided_by or settings.default_csm_id
    try:
        apr = approvals.decide_approval(
            approval_id=approval_id,
            decision=body.decision,
            decided_by=body.decided_by or csm,
            note=body.note,
            csm_id=csm,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Execute on approve via gateway when applicable
    if body.decision == "approved":
        gw = get_gateway()
        payload = apr.payload or {}
        if apr.action_type == "external_email":
            # Draft already created; still do not send
            pass
        elif apr.action_type == "slack_escalate":
            gw.post_slack(channel="#cs-escalations", text=str(payload.get("summary") or apr.title))
        elif apr.action_type == "create_task":
            gw.create_hubspot_task(
                account_id=apr.account_id or "",
                title=apr.title,
                body=str(payload.get("body") or ""),
            )
    return apr
