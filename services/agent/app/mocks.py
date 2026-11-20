"""In-memory fixtures matching contracts.py for MOCK_MODE and web development."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.contracts import (
    Account,
    AccountStatus,
    Approval,
    ApprovalStatus,
    BriefingItem,
    CSM,
    CSMPreferences,
    DailyBriefing,
    MockBundle,
    PreferredChannel,
    RiskSignal,
)

DEMO_CSM = CSM(
    csm_id="csm_demo_001",
    email="alex@nudge.local",
    full_name="Alex Rivera",
)


def build_mock_bundle(csm_id: str = "csm_demo_001") -> MockBundle:
    now = datetime.now(timezone.utc)
    accounts = [
        Account(
            account_id="acc_acme",
            name="Acme Analytics",
            industry="SaaS",
            arr=120000,
            plan_tier="Growth",
            renewal_date=date.today() + timedelta(days=28),
            health_score=0.42,
            status=AccountStatus.CHURN_RISK,
            owner_csm_id=csm_id,
        ),
        Account(
            account_id="acc_bright",
            name="BrightPath Health",
            industry="Healthcare",
            arr=86000,
            plan_tier="Pro",
            renewal_date=date.today() + timedelta(days=90),
            health_score=0.71,
            status=AccountStatus.ACTIVE,
            owner_csm_id=csm_id,
        ),
        Account(
            account_id="acc_northstar",
            name="Northstar Retail",
            industry="Retail",
            arr=210000,
            plan_tier="Enterprise",
            renewal_date=date.today() + timedelta(days=45),
            health_score=0.55,
            status=AccountStatus.EXPANSION,
            owner_csm_id=csm_id,
        ),
        Account(
            account_id="acc_edge_discount",
            name="Discount Seekers",
            industry="SaaS",
            arr=41000,
            plan_tier="Growth",
            renewal_date=date.today() + timedelta(days=20),
            health_score=0.48,
            status=AccountStatus.CHURN_RISK,
            owner_csm_id=csm_id,
        ),
    ]
    risks = [
        RiskSignal(
            account_id="acc_acme",
            owner_csm_id=csm_id,
            name="Acme Analytics",
            arr=120000,
            renewal_date=accounts[0].renewal_date,
            usage_delta_30d=-0.32,
            open_tickets=3,
            days_to_renewal=28,
            failed_payments=1,
            risk_score=0.78,
            reasons=["Usage down 32% vs prior 30d", "Renewal in 28 days", "1 failed payment"],
        ),
        RiskSignal(
            account_id="acc_bright",
            owner_csm_id=csm_id,
            name="BrightPath Health",
            arr=86000,
            renewal_date=accounts[1].renewal_date,
            usage_delta_30d=-0.08,
            open_tickets=1,
            days_to_renewal=90,
            failed_payments=0,
            risk_score=0.41,
            reasons=["Slight usage dip", "1 open ticket"],
        ),
        RiskSignal(
            account_id="acc_northstar",
            owner_csm_id=csm_id,
            name="Northstar Retail",
            arr=210000,
            renewal_date=accounts[2].renewal_date,
            usage_delta_30d=0.12,
            open_tickets=2,
            days_to_renewal=45,
            failed_payments=0,
            risk_score=0.52,
            reasons=["Open tickets on SSO", "Expansion signal vs support load"],
        ),
        RiskSignal(
            account_id="acc_edge_discount",
            owner_csm_id=csm_id,
            name="Discount Seekers",
            arr=41000,
            renewal_date=accounts[3].renewal_date,
            usage_delta_30d=-0.15,
            open_tickets=1,
            days_to_renewal=20,
            failed_payments=0,
            risk_score=0.58,
            reasons=["Asking for discount", "Renewal in 20 days"],
        ),
    ]
    # Briefing highlights top 3; accounts list may include edge fixtures
    briefing_pairs = list(zip(accounts, risks))[:3]
    items = [
        BriefingItem(
            account=a,
            risk=r,
            top_reasons=r.reasons,
            recommended_next_step="Review hybrid context and propose outreach plan",
        )
        for a, r in briefing_pairs
    ]
    briefing = DailyBriefing(
        csm_id=csm_id,
        generated_at=now,
        items=items,
        summary="Three accounts need attention; Acme is highest risk before renewal.",
    )
    approvals = [
        Approval(
            approval_id="apr_001",
            csm_id=csm_id,
            account_id="acc_acme",
            action_type="external_email",
            title="Draft: check-in before renewal",
            description="Email draft pending approval — will not send until approved.",
            payload={"to": "csm-contact@acme.example", "subject": "Quick check-in"},
            status=ApprovalStatus.PENDING,
            created_at=now - timedelta(hours=2),
        )
    ]
    return MockBundle(
        csm=DEMO_CSM.model_copy(update={"csm_id": csm_id}),
        preferences=CSMPreferences(
            csm_id=csm_id,
            preferred_channel=PreferredChannel.EMAIL,
            risk_threshold=0.6,
        ),
        briefing=briefing,
        accounts=accounts,
        approvals=approvals,
    )
