from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentOrchestrator
from app.database import get_db
from app.models.schemas import AgentCreate, AgentPatch, MessageCreate
from app.services import agents as agent_service
from app.services.carts import get_or_create_cart, to_public_cart
from app.services.events import to_public
from app.models.entities import ConversationMessage
from sqlalchemy import select

router = APIRouter(prefix="/api/agents", tags=["agents"])
orchestrator = AgentOrchestrator()


@router.get("")
def list_agents(db: Session = Depends(get_db)):
    return [agent_service.to_public(a).model_dump() for a in agent_service.list_agents(db)]


@router.post("")
def create_agent(body: AgentCreate, db: Session = Depends(get_db)):
    agent = agent_service.create_agent(db, body)
    return agent_service.to_public(agent).model_dump()


@router.get("/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(404, "Agent not found")
    cart = get_or_create_cart(db, agent.customer_id)
    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.agent_id == agent.id)
            .order_by(ConversationMessage.created_at)
        )
    )
    return {
        **agent_service.to_public(agent).model_dump(),
        "cart": to_public_cart(cart).model_dump(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_name": m.tool_name,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "xray": agent_service.xray_payload(agent),
        "attack_result": agent_service.attack_result_payload(agent),
    }


@router.patch("/{agent_id}")
def patch_agent(agent_id: str, body: AgentPatch, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(404, "Agent not found")
    agent = agent_service.patch_agent(db, agent, body)
    return agent_service.to_public(agent).model_dump()


@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(404, "Agent not found")
    agent_service.delete_agent(db, agent)
    return {"deleted": True, "id": agent_id}


@router.post("/{agent_id}/reset")
def reset_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(404, "Agent not found")
    agent = agent_service.reset_agent(db, agent)
    return agent_service.to_public(agent).model_dump()


@router.post("/{agent_id}/messages")
async def post_message(agent_id: str, body: MessageCreate, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(404, "Agent not found")
    if not body.content.strip():
        raise HTTPException(400, "Message is empty")
    outcome = await orchestrator.handle_user_message(db, agent, body.content.strip())
    cart = get_or_create_cart(db, agent.customer_id)
    return {
        **outcome,
        "agent": agent_service.to_public(agent).model_dump(),
        "cart": to_public_cart(cart).model_dump(),
    }


@router.get("/{agent_id}/events")
def list_events(agent_id: str, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(404, "Agent not found")
    events = sorted(agent.events, key=lambda e: e.created_at)
    return [to_public(e).model_dump() for e in events]
