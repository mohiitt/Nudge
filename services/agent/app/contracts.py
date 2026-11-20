"""Shared Pydantic contracts for Nudge agent, web UI, and evals.

All agents must import these models (or mirror their JSON shapes) rather than
inventing parallel schemas. Ownership is always expressed via csm_id / owner_csm_id.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AccountStatus(str, Enum):
    ACTIVE = "active"
    CHURN_RISK = "churn_risk"
    CHURNED = "churned"
    EXPANSION = "expansion"


class TicketStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    SOLVED = "solved"
    CLOSED = "closed"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    SKIPPED = "skipped"


class InterventionOutcome(str, Enum):
    PENDING = "pending"
    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    WORSENED = "worsened"
    UNKNOWN = "unknown"


class PreferredChannel(str, Enum):
    EMAIL = "email"
    CALL = "call"
    SLACK = "slack"
    LINKEDIN = "linkedin"


SensitiveActionType = Literal[
    "external_email",
    "discount",
    "contract_change",
    "refund",
    "slack_escalate",
    "create_task",
]


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------


class CSM(BaseModel):
    csm_id: str
    email: str
    full_name: str
    timezone: str = "America/Los_Angeles"


class CSMPreferences(BaseModel):
    csm_id: str
    preferred_channel: PreferredChannel = PreferredChannel.EMAIL
    briefing_hour_local: int = 8
    risk_threshold: float = 0.60
    prefs_json: Optional[dict[str, Any]] = None


class Account(BaseModel):
    account_id: str
    name: str
    industry: Optional[str] = None
    arr: float = 0.0
    plan_tier: Optional[str] = None
    renewal_date: Optional[date] = None
    health_score: Optional[float] = None
    status: AccountStatus = AccountStatus.ACTIVE
    owner_csm_id: str


class RiskSignal(BaseModel):
    account_id: str
    owner_csm_id: str
    name: str
    arr: float = 0.0
    renewal_date: Optional[date] = None
    usage_delta_30d: float = 0.0
    open_tickets: int = 0
    days_to_renewal: Optional[int] = None
    failed_payments: int = 0
    risk_score: float
    reasons: list[str] = Field(default_factory=list)


class TicketChunk(BaseModel):
    chunk_id: str
    account_id: str
    owner_csm_id: str
    ticket_id: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime
    text_redacted: str
    similarity: Optional[float] = None


class SimilarAccount(BaseModel):
    account_id: str
    name: str
    similarity: float
    intervention_summary: Optional[str] = None
    outcome: Optional[InterventionOutcome] = None


class Recommendation(BaseModel):
    recommendation_id: str
    account_id: str
    owner_csm_id: str
    title: str
    rationale: str
    suggested_actions: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    risk_score: Optional[float] = None


class BriefingItem(BaseModel):
    account: Account
    risk: RiskSignal
    top_reasons: list[str] = Field(default_factory=list)
    recommended_next_step: Optional[str] = None


class DailyBriefing(BaseModel):
    csm_id: str
    generated_at: datetime
    items: list[BriefingItem] = Field(default_factory=list)
    summary: str = ""


class AccountDeepDive(BaseModel):
    account: Account
    risk: RiskSignal
    usage_delta_30d: float
    open_tickets: int
    recent_tickets: list[TicketChunk] = Field(default_factory=list)
    similar_accounts: list[SimilarAccount] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    recent_activities: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Actions & approvals
# ---------------------------------------------------------------------------


class ActionRequest(BaseModel):
    """Proposed action from the agent; may require approval before execution."""

    action_id: str
    csm_id: str
    account_id: Optional[str] = None
    action_type: str
    tool_name: str
    title: str
    description: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    status: ActionStatus = ActionStatus.PROPOSED


class Approval(BaseModel):
    approval_id: str
    csm_id: str
    account_id: Optional[str] = None
    action_type: str
    title: str
    description: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class ApprovalDecision(BaseModel):
    approval_id: str
    decision: Literal["approved", "rejected"]
    decided_by: str
    note: Optional[str] = None


class Intervention(BaseModel):
    intervention_id: str
    account_id: str
    owner_csm_id: str
    action_type: str
    summary: str
    plan: Optional[dict[str, Any]] = None
    outcome: InterventionOutcome = InterventionOutcome.PENDING
    outcome_measured_at: Optional[datetime] = None
    created_at: datetime


class AgentMemoryEntry(BaseModel):
    memory_id: str
    csm_id: str
    account_id: Optional[str] = None
    memory_type: Literal["preference", "fact", "outcome", "note"]
    content: str
    created_at: datetime
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Chat / Firedrill http.v1
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Firedrill http.v1 compatible: POST {"message","session"}."""

    message: str
    session: Optional[str] = None
    csm_id: Optional[str] = None  # optional extension; defaults from session/config


class ChatResponse(BaseModel):
    reply: str
    session: Optional[str] = None
    actions: list[ActionRequest] = Field(default_factory=list)
    approvals: list[Approval] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool I/O shapes (agent tools)
# ---------------------------------------------------------------------------


class GetBriefingArgs(BaseModel):
    csm_id: str
    limit: int = 5


class GetAccountRiskArgs(BaseModel):
    csm_id: str
    account_id: str


class FindSimilarAccountsArgs(BaseModel):
    csm_id: str
    account_id: str
    limit: int = 5


class DraftMessageArgs(BaseModel):
    csm_id: str
    account_id: str
    channel: PreferredChannel = PreferredChannel.EMAIL
    intent: str
    tone: Optional[str] = None


class EscalateArgs(BaseModel):
    csm_id: str
    account_id: str
    channel: Literal["slack"] = "slack"
    summary: str
    urgency: Literal["low", "medium", "high"] = "medium"


class CreateTaskArgs(BaseModel):
    csm_id: str
    account_id: str
    title: str
    body: Optional[str] = None
    due_date: Optional[date] = None


# ---------------------------------------------------------------------------
# Mock fixtures helpers (web / Firedrill)
# ---------------------------------------------------------------------------


class MockBundle(BaseModel):
    """Bundle of mocked contract objects for UI and local demos."""

    csm: CSM
    preferences: CSMPreferences
    briefing: DailyBriefing
    accounts: list[Account] = Field(default_factory=list)
    approvals: list[Approval] = Field(default_factory=list)
