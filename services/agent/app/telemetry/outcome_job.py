"""Outcome tracking job — updates interventions and emits Amplitude events."""

from __future__ import annotations

from datetime import datetime, timezone

from app.data import db
from app.mocks import build_mock_bundle
from app.telemetry.events import intervention_outcome_measured, track


def run(csm_id: str = "csm_demo_001") -> int:
    rows = db.fetch_all(
        """
        SELECT intervention_id, account_id, owner_csm_id, outcome, created_at
        FROM interventions
        WHERE owner_csm_id = %(csm_id)s AND outcome = 'pending'
        """,
        {"csm_id": csm_id},
    )
    if not rows:
        # Mock dry-run
        bundle = build_mock_bundle(csm_id)
        updated = 0
        for item in bundle.briefing.items:
            intervention_outcome_measured(
                csm_id,
                f"int_{item.account.account_id}_0",
                "improved" if item.risk.risk_score < 0.5 else "unchanged",
                days_since=14,
            )
            updated += 1
        track("job.outcome_tracking_completed", csm_id, {"updated_count": updated})
        get_amp = __import__("app.telemetry.amplitude", fromlist=["get_amplitude"]).get_amplitude
        get_amp().flush()
        print(f"[dry-run] measured {updated} mock interventions")
        return updated

    updated = 0
    now = datetime.now(timezone.utc)
    for r in rows:
        created = r.get("created_at") or now
        if hasattr(created, "tzinfo") and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days = max(0, (now - created).days) if hasattr(created, "day") else 14
        outcome = "improved" if days >= 14 else "pending"
        if outcome == "pending":
            continue
        db.execute(
            """
            UPDATE interventions
            SET outcome=%(outcome)s, outcome_measured_at=%(ts)s
            WHERE intervention_id=%(id)s AND owner_csm_id=%(csm_id)s
            """,
            {"outcome": outcome, "ts": now, "id": r["intervention_id"], "csm_id": csm_id},
        )
        intervention_outcome_measured(csm_id, r["intervention_id"], outcome, days_since=days)
        updated += 1
    track("job.outcome_tracking_completed", csm_id, {"updated_count": updated})
    from app.telemetry.amplitude import get_amplitude

    get_amplitude().flush()
    print(f"Updated {updated} interventions")
    return updated


if __name__ == "__main__":
    run()
