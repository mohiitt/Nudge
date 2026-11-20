"""Write account_health_snapshots from v_account_risk_signals."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Allow running as script
REPO = Path(__file__).resolve().parents[3]
AGENT = REPO / "services" / "agent"
if str(AGENT) not in sys.path:
    sys.path.insert(0, str(AGENT))

from app.data import db  # noqa: E402
from app.mocks import build_mock_bundle  # noqa: E402


def run(csm_id: str | None = None) -> int:
    csm_id = csm_id or os.getenv("DEFAULT_CSM_ID", "csm_demo_001")
    rows = db.fetch_all(
        """
        SELECT account_id, owner_csm_id, usage_delta_30d, open_tickets, days_to_renewal,
               failed_payments, risk_score
        FROM v_account_risk_signals
        WHERE (%(csm_id)s IS NULL OR owner_csm_id = %(csm_id)s)
        """,
        {"csm_id": csm_id},
    )
    if not rows:
        bundle = build_mock_bundle(csm_id)
        print(f"[dry-run] would snapshot {len(bundle.briefing.items)} mock accounts for {csm_id}")
        for item in bundle.briefing.items:
            print(
                f"  {item.account.account_id}: risk={item.risk.risk_score:.2f} "
                f"usage_delta={item.risk.usage_delta_30d:.2f}"
            )
        return len(bundle.briefing.items)

    count = 0
    for r in rows:
        health = max(0.0, 1.0 - float(r["risk_score"]))
        db.execute(
            """
            INSERT INTO account_health_snapshots (
              account_id, owner_csm_id, snapshot_at, health_score, risk_score,
              usage_delta_30d, open_tickets, days_to_renewal, failed_payments, reasons_json
            ) VALUES (
              %(account_id)s, %(owner_csm_id)s, %(snapshot_at)s, %(health_score)s, %(risk_score)s,
              %(usage_delta_30d)s, %(open_tickets)s, %(days_to_renewal)s, %(failed_payments)s, %(reasons_json)s
            )
            """,
            {
                "account_id": r["account_id"],
                "owner_csm_id": r["owner_csm_id"],
                "snapshot_at": datetime.now(timezone.utc),
                "health_score": health,
                "risk_score": r["risk_score"],
                "usage_delta_30d": r.get("usage_delta_30d"),
                "open_tickets": r.get("open_tickets") or 0,
                "days_to_renewal": r.get("days_to_renewal"),
                "failed_payments": r.get("failed_payments") or 0,
                "reasons_json": "[]",
            },
        )
        count += 1
    print(f"Wrote {count} health snapshots at {datetime.now(timezone.utc).isoformat()}")
    return count


if __name__ == "__main__":
    run()
