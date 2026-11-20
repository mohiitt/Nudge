"""Approval state machine and sensitive-action policy checks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from app.contracts import Approval, ApprovalStatus
from app.mocks import build_mock_bundle

# Always require approval — never execute until approved.
HARDCODED_SENSITIVE: frozenset[str] = frozenset(
    {
        "external_email",
        "discount",
        "contract_change",
        "refund",
    }
)

# Default approval_policies when no per-CSM row exists.
DEFAULT_POLICIES: dict[str, bool] = {
    "external_email": True,
    "discount": True,
    "contract_change": True,
    "refund": True,
    "slack_escalate": True,
    "create_task": False,
}

# Per-CSM overrides: csm_id → {action_type → requires_approval}
_POLICY_OVERRIDES: dict[str, dict[str, bool]] = {}

# In-memory approval store
_APPROVALS: dict[str, Approval] = {}
_SEEDED_CSMS: set[str] = set()


def _seed_from_mocks(csm_id: str) -> None:
    if csm_id in _SEEDED_CSMS:
        return
    bundle = build_mock_bundle(csm_id)
    for apr in bundle.approvals:
        _APPROVALS[apr.approval_id] = apr
    _SEEDED_CSMS.add(csm_id)


def set_policy(csm_id: str, action_type: str, requires_approval: bool) -> None:
    _POLICY_OVERRIDES.setdefault(csm_id, {})[action_type] = requires_approval


def requires_approval(csm_id: str, action_type: str) -> bool:
    """Policy check: hardcoded sensitive list + per-CSM approval_policies."""
    if action_type in HARDCODED_SENSITIVE:
        return True
    overrides = _POLICY_OVERRIDES.get(csm_id, {})
    if action_type in overrides:
        return overrides[action_type]
    return DEFAULT_POLICIES.get(action_type, True)


def create_approval(
    *,
    csm_id: str,
    action_type: str,
    title: str,
    description: Optional[str] = None,
    account_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    expires_in_hours: int = 48,
) -> Approval:
    """Create a pending approval_request. Does not execute the action."""
    _seed_from_mocks(csm_id)
    now = datetime.now(timezone.utc)
    approval = Approval(
        approval_id=f"apr_{uuid4().hex[:12]}",
        csm_id=csm_id,
        account_id=account_id,
        action_type=action_type,
        title=title,
        description=description,
        payload=payload or {},
        status=ApprovalStatus.PENDING,
        created_at=now,
        expires_at=now + timedelta(hours=expires_in_hours),
    )
    _APPROVALS[approval.approval_id] = approval
    return approval


def get_approval(approval_id: str) -> Optional[Approval]:
    expire_stale()
    return _APPROVALS.get(approval_id)


def list_approvals(
    *,
    csm_id: str,
    status: Optional[ApprovalStatus] = None,
) -> list[Approval]:
    _seed_from_mocks(csm_id)
    expire_stale()
    rows = [a for a in _APPROVALS.values() if a.csm_id == csm_id]
    if status is not None:
        rows = [a for a in rows if a.status == status]
    rows.sort(key=lambda a: a.created_at, reverse=True)
    return rows


def expire_stale(now: Optional[datetime] = None) -> int:
    """pending → expired when past expires_at. Returns count expired."""
    now = now or datetime.now(timezone.utc)
    count = 0
    for apr in _APPROVALS.values():
        if apr.status != ApprovalStatus.PENDING:
            continue
        if apr.expires_at and apr.expires_at < now:
            apr.status = ApprovalStatus.EXPIRED
            count += 1
    return count


def decide_approval(
    *,
    approval_id: str,
    decision: str,
    decided_by: str,
    note: Optional[str] = None,
    csm_id: Optional[str] = None,
) -> Approval:
    """
    State machine: pending → approved | rejected.
    Expired/already-decided approvals raise ValueError.
    When csm_id is provided, the caller must own the approval (ownership_boundary).
    """
    expire_stale()
    apr = _APPROVALS.get(approval_id)
    if apr is None:
        raise KeyError(f"approval not found: {approval_id}")
    if csm_id is not None and apr.csm_id != csm_id:
        raise PermissionError("ownership_boundary: approval belongs to another CSM")
    if apr.status == ApprovalStatus.EXPIRED:
        raise ValueError("approval has expired")
    if apr.status != ApprovalStatus.PENDING:
        raise ValueError(f"approval already {apr.status.value}")
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be 'approved' or 'rejected'")

    apr.status = ApprovalStatus.APPROVED if decision == "approved" else ApprovalStatus.REJECTED
    apr.decided_by = decided_by
    apr.decided_at = datetime.now(timezone.utc)
    if note:
        apr.payload = {**apr.payload, "decision_note": note}
    return apr


def clear_approvals() -> None:
    """Test helper."""
    _APPROVALS.clear()
    _SEEDED_CSMS.clear()
