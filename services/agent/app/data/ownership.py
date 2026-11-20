"""Ownership enforcement — never rely on the LLM prompt alone."""

from __future__ import annotations

from app.data import db
from app.mocks import build_mock_bundle


class OwnershipError(PermissionError):
    """CSM does not own the requested account."""


def assert_owns_account(csm_id: str, account_id: str) -> None:
    rows = db.fetch_all(
        """
        SELECT account_id FROM accounts
        WHERE account_id = %(account_id)s AND owner_csm_id = %(csm_id)s
        LIMIT 1
        """,
        {"account_id": account_id, "csm_id": csm_id},
    )
    if rows:
        return

    # Mock path
    if not db.get_connection():
        bundle = build_mock_bundle(csm_id)
        if any(a.account_id == account_id and a.owner_csm_id == csm_id for a in bundle.accounts):
            return
        # Known other-owner edge case
        if account_id == "acc_edge_ownership":
            raise OwnershipError(f"CSM {csm_id} does not own account {account_id}")
        # If account unknown in mocks but not the edge case, still deny unless in bundle
        raise OwnershipError(f"CSM {csm_id} does not own account {account_id}")

    raise OwnershipError(f"CSM {csm_id} does not own account {account_id}")
