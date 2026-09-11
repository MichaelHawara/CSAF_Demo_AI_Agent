"""Agent instance lifecycle. Creating an agent never trains a model."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import (
    AgentInstance,
    ConversationMessage,
    PendingCheckout,
    SecurityEvent,
)
from app.models.schemas import AgentCreate, AgentPatch, AgentPublic
from app.services.carts import clear_cart, get_or_create_cart
from app.services.constants import DEFAULT_ALLOWED_TOOLS, DEFAULT_SYSTEM_INSTRUCTION, DEMO_CUSTOMER_ID
from app.agents.orchestrator import provider_note


def allowed_tool_list(agent: AgentInstance) -> list[str]:
    return [part.strip() for part in (agent.allowed_tools or "").split(",") if part.strip()]


def to_public(agent: AgentInstance) -> AgentPublic:
    settings = get_settings()
    return AgentPublic(
        id=agent.id,
        customer_id=agent.customer_id,
        display_name=agent.display_name,
        provider=agent.provider,
        model=agent.model,
        mode=agent.mode,
        system_instruction=agent.system_instruction,
        allowed_tools=allowed_tool_list(agent),
        budget=agent.budget,
        max_quantity=agent.max_quantity,
        status=agent.status,
        created_at=agent.created_at.isoformat() if agent.created_at else "",
        gemini_available=settings.gemini_configured,
        provider_note=provider_note(agent),
    )


def list_agents(db: Session) -> list[AgentInstance]:
    return list(db.scalars(select(AgentInstance).order_by(AgentInstance.created_at)))


def get_agent(db: Session, agent_id: str) -> AgentInstance | None:
    return db.get(AgentInstance, agent_id)


def create_agent(db: Session, body: AgentCreate) -> AgentInstance:
    settings = get_settings()
    provider = body.provider
    model = settings.gemini_model if provider == "gemini" else "mock-deterministic"
    agent = AgentInstance(
        id=f"agent_{uuid.uuid4().hex[:10]}",
        customer_id=body.customer_id or DEMO_CUSTOMER_ID,
        display_name=body.display_name,
        provider=provider,
        model=model,
        mode=body.mode,
        system_instruction=body.system_instruction or DEFAULT_SYSTEM_INSTRUCTION,
        allowed_tools=",".join(DEFAULT_ALLOWED_TOOLS),
        budget=body.budget,
        max_quantity=body.max_quantity,
        created_at=datetime.now(timezone.utc),
    )
    db.add(agent)
    get_or_create_cart(db, agent.customer_id)
    db.commit()
    db.refresh(agent)
    return agent


def patch_agent(db: Session, agent: AgentInstance, body: AgentPatch) -> AgentInstance:
    settings = get_settings()
    if body.display_name is not None:
        agent.display_name = body.display_name
    if body.provider is not None:
        agent.provider = body.provider
        agent.model = settings.gemini_model if body.provider == "gemini" else "mock-deterministic"
    if body.mode is not None:
        agent.mode = body.mode
    if body.budget is not None:
        agent.budget = body.budget
    if body.max_quantity is not None:
        agent.max_quantity = body.max_quantity
    if body.system_instruction is not None:
        agent.system_instruction = body.system_instruction
    if body.model is not None:
        agent.model = body.model
    db.commit()
    db.refresh(agent)
    return agent


def reset_agent(db: Session, agent: AgentInstance) -> AgentInstance:
    for message in list(agent.messages):
        db.delete(message)
    for event in list(agent.events):
        db.delete(event)
    pendings = db.scalars(
        select(PendingCheckout).where(PendingCheckout.customer_id == agent.customer_id)
    )
    for pending in pendings:
        db.delete(pending)
    cart = get_or_create_cart(db, agent.customer_id)
    clear_cart(db, cart)
    agent.mock_phase = 0
    agent.last_xray_json = "{}"
    agent.last_attempt_json = "{}"
    agent.last_result_json = "{}"
    agent.status = "idle"
    db.commit()
    db.refresh(agent)
    return agent


def delete_agent(db: Session, agent: AgentInstance) -> None:
    db.query(ConversationMessage).filter(ConversationMessage.agent_id == agent.id).delete()
    db.query(SecurityEvent).filter(SecurityEvent.agent_id == agent.id).delete()
    db.delete(agent)
    db.commit()


def xray_payload(agent: AgentInstance) -> dict:
    try:
        return json.loads(agent.last_xray_json or "{}")
    except json.JSONDecodeError:
        return {}


def attack_result_payload(agent: AgentInstance) -> dict:
    try:
        return json.loads(agent.last_result_json or "{}")
    except json.JSONDecodeError:
        return {}
