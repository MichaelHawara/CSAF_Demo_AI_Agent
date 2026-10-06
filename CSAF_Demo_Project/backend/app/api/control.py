from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.schemas import AgentCreate
from app.services import agents as agent_service
from app.services.constants import (
    DEFAULT_ALLOWED_TOOLS,
    DEFAULT_SYSTEM_INSTRUCTION,
    DEMO_AGENT_ID,
    DEMO_CUSTOMER_ID,
    DEMO_REQUEST,
)
from app.services.carts import get_or_create_cart, to_public_cart
from app.seed import seed_database
from app.models.entities import AgentInstance

router = APIRouter(prefix="/api/control", tags=["control"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    settings = get_settings()
    agent = db.get(AgentInstance, DEMO_AGENT_ID)
    return {
        "gemini_configured": settings.gemini_configured,
        "effective_provider": settings.effective_provider,
        "requested_provider": settings.agent_provider,
        "demo_agent_id": DEMO_AGENT_ID,
        "demo_customer_id": DEMO_CUSTOMER_ID,
        "demo_request": DEMO_REQUEST,
        "budget": 80.0,
        "max_quantity": 1,
        "checkout_confirmation": "Required",
        "deterministic_demo_mode": not settings.gemini_configured or settings.effective_provider == "mock",
        "demo_agent": agent_service.to_public(agent).model_dump() if agent else None,
        "allowed_tools": DEFAULT_ALLOWED_TOOLS,
        "reserved_endpoints": {
            "GET /api/profile/{customer_id}": "TODO(STUDENT) fictional profile",
            "GET /api/history/{customer_id}": "TODO(STUDENT) fictional purchase history",
            "POST /api/attacker-inbox": "TODO(STUDENT) mock attacker inbox",
            "GET /api/memory/{agent_id}": "TODO(STUDENT) memory inspector",
        },
    }


@router.post("/load-demo")
def load_demo(db: Session = Depends(get_db)):
    seed_database(db)
    agent = db.get(AgentInstance, DEMO_AGENT_ID)
    if agent is None:
        agent = agent_service.create_agent(
            db,
            AgentCreate(
                display_name="Alex",
                customer_id=DEMO_CUSTOMER_ID,
                provider="mock",
                mode="vulnerable",
                budget=80.0,
                max_quantity=1,
                system_instruction=DEFAULT_SYSTEM_INSTRUCTION,
            ),
        )
        agent.id = DEMO_AGENT_ID
        db.commit()
        db.refresh(agent)
    agent = agent_service.reset_agent(db, agent)
    cart = get_or_create_cart(db, DEMO_CUSTOMER_ID)
    return {
        "agent": agent_service.to_public(agent).model_dump(),
        "cart": to_public_cart(cart).model_dump(),
        "demo_request": DEMO_REQUEST,
        "budget": 80.0,
        "max_quantity": 1,
        "checkout_confirmation": "Required",
        "message": "Demo reset. Load the prepared request in Alex's panel and send it.",
    }


@router.post("/reset-demo")
def reset_demo(db: Session = Depends(get_db)):
    return load_demo(db)
