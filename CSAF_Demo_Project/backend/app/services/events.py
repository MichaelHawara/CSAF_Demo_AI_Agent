"""Activity-monitor events.

Every tool call and policy decision should produce a row. Details are
sanitized so a projector view cannot leak configured secrets.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.entities import SecurityEvent
from app.models.schemas import SecurityEventPublic
from app.security.redact import dumps_sanitized, sanitize_text


def log_event(
    db: Session,
    *,
    agent_id: str,
    customer_id: str,
    actor: str,
    message: str,
    details: dict | str | None = None,
    step: int = 0,
) -> SecurityEvent:
    payload = details if isinstance(details, str) else dumps_sanitized(details or {})
    event = SecurityEvent(
        id=f"evt_{uuid.uuid4().hex[:12]}",
        agent_id=agent_id,
        customer_id=customer_id,
        actor=actor.upper(),
        message=sanitize_text(message),
        details=payload,
        step=step,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event


def format_event(event: SecurityEvent) -> str:
    stamp = event.created_at.astimezone(timezone.utc).strftime("%H:%M:%S")
    actor = f"{event.actor:<9}"
    return f"[{stamp}] {actor} {event.message}"


def to_public(event: SecurityEvent) -> SecurityEventPublic:
    created = event.created_at.isoformat()
    return SecurityEventPublic(
        id=event.id,
        actor=event.actor,
        message=event.message,
        details=event.details,
        step=event.step,
        created_at=created,
        formatted=format_event(event),
    )
