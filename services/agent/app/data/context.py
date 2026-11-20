"""Hybrid context queries with ownership filters. Falls back to mocks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.contracts import (
    Account,
    AccountDeepDive,
    AccountStatus,
    BriefingItem,
    DailyBriefing,
    Recommendation,
    RiskSignal,
    SimilarAccount,
    TicketChunk,
)
from app.data import db
from app.data.ownership import OwnershipError, assert_owns_account
from app.mocks import build_mock_bundle

HYBRID_SQL = """
SELECT a.account_id, a.name, a.arr, a.renewal_date, a.owner_csm_id, a.status, a.plan_tier, a.health_score,
       r.usage_delta_30d, r.open_tickets, r.days_to_renewal, r.failed_payments, r.risk_score,
       t.ticket_id, t.chunk_id, t.category, t.sentiment, t.created_at, t.text_redacted,
       t.embedding <*> %(qvec)s AS sim
FROM v_account_risk_signals r
JOIN accounts a USING (account_id)
LEFT JOIN ticket_chunks t
  ON t.account_id = a.account_id
 AND t.owner_csm_id = %(csm_id)s
 AND t.created_at > NOW() - INTERVAL 30 DAY
WHERE a.owner_csm_id = %(csm_id)s
ORDER BY r.risk_score DESC, sim DESC
LIMIT %(limit)s
"""


def _risk_from_mock(bundle, account_id: str) -> RiskSignal:
    for item in bundle.briefing.items:
        if item.account.account_id == account_id:
            return item.risk
    raise KeyError(account_id)


def get_briefing(csm_id: str, limit: int = 5) -> DailyBriefing:
    rows = db.fetch_all(
        """
        SELECT account_id, owner_csm_id, name, arr, renewal_date, usage_delta_30d,
               open_tickets, days_to_renewal, failed_payments, risk_score
        FROM v_account_risk_signals
        WHERE owner_csm_id = %(csm_id)s
        ORDER BY risk_score DESC
        LIMIT %(limit)s
        """,
        {"csm_id": csm_id, "limit": limit},
    )
    if not rows:
        bundle = build_mock_bundle(csm_id)
        items = bundle.briefing.items[:limit]
        return DailyBriefing(
            csm_id=csm_id,
            generated_at=datetime.now(timezone.utc),
            items=items,
            summary=bundle.briefing.summary,
        )

    items: list[BriefingItem] = []
    for r in rows:
        reasons = []
        if (r.get("usage_delta_30d") or 0) < -0.1:
            reasons.append(f"Usage delta {r['usage_delta_30d']:.0%}")
        if (r.get("open_tickets") or 0) > 0:
            reasons.append(f"{r['open_tickets']} open tickets")
        if r.get("days_to_renewal") is not None and r["days_to_renewal"] <= 45:
            reasons.append(f"Renewal in {r['days_to_renewal']} days")
        if (r.get("failed_payments") or 0) > 0:
            reasons.append(f"{r['failed_payments']} failed payments")
        risk = RiskSignal(
            account_id=r["account_id"],
            owner_csm_id=r["owner_csm_id"],
            name=r["name"],
            arr=float(r.get("arr") or 0),
            renewal_date=r.get("renewal_date"),
            usage_delta_30d=float(r.get("usage_delta_30d") or 0),
            open_tickets=int(r.get("open_tickets") or 0),
            days_to_renewal=r.get("days_to_renewal"),
            failed_payments=int(r.get("failed_payments") or 0),
            risk_score=float(r.get("risk_score") or 0),
            reasons=reasons,
        )
        account = Account(
            account_id=r["account_id"],
            name=r["name"],
            arr=float(r.get("arr") or 0),
            renewal_date=r.get("renewal_date"),
            status=AccountStatus.CHURN_RISK if risk.risk_score >= 0.6 else AccountStatus.ACTIVE,
            owner_csm_id=csm_id,
        )
        items.append(
            BriefingItem(
                account=account,
                risk=risk,
                top_reasons=reasons,
                recommended_next_step="Review hybrid context and propose a plan",
            )
        )
    return DailyBriefing(
        csm_id=csm_id,
        generated_at=datetime.now(timezone.utc),
        items=items,
        summary=f"{len(items)} accounts ranked by risk for {csm_id}",
    )


def get_account_risk(csm_id: str, account_id: str) -> RiskSignal:
    assert_owns_account(csm_id, account_id)
    rows = db.fetch_all(
        """
        SELECT * FROM v_account_risk_signals
        WHERE owner_csm_id = %(csm_id)s AND account_id = %(account_id)s
        LIMIT 1
        """,
        {"csm_id": csm_id, "account_id": account_id},
    )
    if rows:
        r = rows[0]
        return RiskSignal(
            account_id=r["account_id"],
            owner_csm_id=r["owner_csm_id"],
            name=r["name"],
            arr=float(r.get("arr") or 0),
            renewal_date=r.get("renewal_date"),
            usage_delta_30d=float(r.get("usage_delta_30d") or 0),
            open_tickets=int(r.get("open_tickets") or 0),
            days_to_renewal=r.get("days_to_renewal"),
            failed_payments=int(r.get("failed_payments") or 0),
            risk_score=float(r.get("risk_score") or 0),
            reasons=[],
        )
    return _risk_from_mock(build_mock_bundle(csm_id), account_id)


def find_similar_interventions(csm_id: str, account_id: str, limit: int = 5) -> list[SimilarAccount]:
    assert_owns_account(csm_id, account_id)
    rows = db.fetch_all(
        """
        SELECT ie.account_id, a.name, ie.summary_text, ie.outcome,
               ie.embedding <*> (
                 SELECT embedding FROM intervention_embeddings
                 WHERE account_id = %(account_id)s AND owner_csm_id = %(csm_id)s
                 LIMIT 1
               ) AS similarity
        FROM intervention_embeddings ie
        JOIN accounts a ON a.account_id = ie.account_id
        WHERE ie.owner_csm_id = %(csm_id)s
          AND ie.account_id <> %(account_id)s
        ORDER BY similarity DESC
        LIMIT %(limit)s
        """,
        {"csm_id": csm_id, "account_id": account_id, "limit": limit},
    )
    if rows:
        return [
            SimilarAccount(
                account_id=r["account_id"],
                name=r["name"],
                similarity=float(r.get("similarity") or 0),
                intervention_summary=r.get("summary_text"),
                outcome=r.get("outcome"),
            )
            for r in rows
        ]
    # Mock similar accounts from briefing peers
    bundle = build_mock_bundle(csm_id)
    peers = [a for a in bundle.accounts if a.account_id != account_id][:limit]
    return [
        SimilarAccount(
            account_id=a.account_id,
            name=a.name,
            similarity=0.8 - i * 0.1,
            intervention_summary="Scheduled QBR + success plan email",
            outcome="improved",
        )
        for i, a in enumerate(peers)
    ]


def hybrid_context(csm_id: str, qvec: Optional[list[float]] = None, limit: int = 50) -> list[dict[str, Any]]:
    """Plan hybrid query; ownership always applied."""
    if db.get_connection() is None:
        briefing = get_briefing(csm_id, limit=min(limit, 10))
        return [
            {
                "account_id": i.account.account_id,
                "name": i.account.name,
                "risk_score": i.risk.risk_score,
                "usage_delta_30d": i.risk.usage_delta_30d,
                "open_tickets": i.risk.open_tickets,
                "reasons": i.top_reasons,
            }
            for i in briefing.items
        ]
    return db.fetch_all(
        HYBRID_SQL,
        {"csm_id": csm_id, "qvec": qvec, "limit": limit},
    )


def get_account_deep_dive(csm_id: str, account_id: str) -> AccountDeepDive:
    assert_owns_account(csm_id, account_id)
    risk = get_account_risk(csm_id, account_id)
    bundle = build_mock_bundle(csm_id)
    account = next((a for a in bundle.accounts if a.account_id == account_id), None)
    if account is None:
        account = Account(
            account_id=account_id,
            name=risk.name,
            arr=risk.arr,
            renewal_date=risk.renewal_date,
            status=AccountStatus.CHURN_RISK,
            owner_csm_id=csm_id,
        )
    similar = find_similar_interventions(csm_id, account_id)
    tickets = [
        TicketChunk(
            chunk_id=f"chk_{account_id}_0",
            account_id=account_id,
            owner_csm_id=csm_id,
            ticket_id=f"tkt_{account_id}_0",
            category="support",
            sentiment="negative",
            created_at=datetime.now(timezone.utc),
            text_redacted="Customer reported friction with recent release.",
            similarity=0.91,
        )
    ]
    recs = [
        Recommendation(
            recommendation_id=f"rec_{uuid4().hex[:8]}",
            account_id=account_id,
            owner_csm_id=csm_id,
            title="Propose check-in plan",
            rationale="; ".join(risk.reasons) or "Elevated risk score",
            suggested_actions=["draft_message", "create_task", "escalate"],
            priority="high" if risk.risk_score >= 0.6 else "medium",
            risk_score=risk.risk_score,
        )
    ]
    return AccountDeepDive(
        account=account,
        risk=risk,
        usage_delta_30d=risk.usage_delta_30d,
        open_tickets=risk.open_tickets,
        recent_tickets=tickets,
        similar_accounts=similar,
        recommendations=recs,
        recent_activities=[],
    )


__all__ = [
    "OwnershipError",
    "assert_owns_account",
    "get_briefing",
    "get_account_risk",
    "find_similar_interventions",
    "hybrid_context",
    "get_account_deep_dive",
]
