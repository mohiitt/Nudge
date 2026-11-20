"""Agent memory read/write. In-memory store is fine for MOCK_MODE."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.contracts import AgentMemoryEntry

# csm_id → list[AgentMemoryEntry]
_STORE: dict[str, list[AgentMemoryEntry]] = {}


def memory_write(
    *,
    csm_id: str,
    content: str,
    memory_type: str = "note",
    account_id: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> AgentMemoryEntry:
    """Persist a memory entry scoped to a CSM (and optional account)."""
    if memory_type not in ("preference", "fact", "outcome", "note"):
        memory_type = "note"
    entry = AgentMemoryEntry(
        memory_id=f"mem_{uuid4().hex[:12]}",
        csm_id=csm_id,
        account_id=account_id,
        memory_type=memory_type,  # type: ignore[arg-type]
        content=content,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    _STORE.setdefault(csm_id, []).append(entry)
    return entry


def memory_read(
    *,
    csm_id: str,
    account_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 20,
) -> list[AgentMemoryEntry]:
    """Return memories for this CSM, optionally filtered by account/type."""
    now = datetime.now(timezone.utc)
    rows = _STORE.get(csm_id, [])
    out: list[AgentMemoryEntry] = []
    for entry in reversed(rows):
        if entry.expires_at and entry.expires_at < now:
            continue
        if account_id and entry.account_id and entry.account_id != account_id:
            continue
        if memory_type and entry.memory_type != memory_type:
            continue
        out.append(entry)
        if len(out) >= limit:
            break
    return out


def memory_to_dicts(entries: list[AgentMemoryEntry]) -> list[dict[str, Any]]:
    return [e.model_dump(mode="json") for e in entries]


def clear_memory(csm_id: Optional[str] = None) -> None:
    """Test helper."""
    if csm_id is None:
        _STORE.clear()
    else:
        _STORE.pop(csm_id, None)
