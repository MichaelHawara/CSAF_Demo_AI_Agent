"""FastAPI entrypoint for the Nozama AI Shopping Assistant.

The browser talks only to this process. Gemini is an optional provider behind
AgentProvider; it never receives a cart object to mutate directly.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api import agents, cart, checkout, control, products
from app.config import get_settings
from app.database import Base, get_engine, get_session_factory
from app.models import entities  # noqa: F401  — register metadata
from app.seed import seed_database
from app.services.agents import reset_agent
from app.services.constants import (
    DEFAULT_ALLOWED_TOOLS,
    DEMO_AGENT_ID,
    is_default_instruction,
    system_instruction_for_mode,
)

"""
from pathlib import Path
from fastapi.staticfiles import StaticFiles
"""


def _ensure_product_url_column(engine) -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("products")}
    if "url" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE products ADD COLUMN url VARCHAR(400) NOT NULL DEFAULT ''")
            )


def _ensure_agent_turn_columns(engine) -> None:
    """Add the per-request counters to agent tables created before they existed."""
    columns = {column["name"] for column in inspect(engine).get_columns("agent_instances")}
    additions = {
        "turn_quantity": "INTEGER NOT NULL DEFAULT 0",
        "turn_spent": "FLOAT NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        for name, ddl in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE agent_instances ADD COLUMN {name} {ddl}"))


def _ensure_checkout_and_attachment_columns(engine) -> None:
    """Add the receipt / chat-card columns to databases created before they existed."""
    additions = {
        "agent_instances": {"last_checkout_json": "TEXT NOT NULL DEFAULT ''"},
        "conversation_messages": {"attachments_json": "TEXT NOT NULL DEFAULT ''"},
    }
    with engine.begin() as connection:
        for table, columns_to_add in additions.items():
            existing = {column["name"] for column in inspect(engine).get_columns(table)}
            for name, ddl in columns_to_add.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def _grant_default_tools(session) -> None:
    """Agents created before a tool existed get it added to their allow-list."""
    for agent in session.query(entities.AgentInstance).all():
        granted = [part.strip() for part in (agent.allowed_tools or "").split(",") if part.strip()]
        missing = [tool for tool in DEFAULT_ALLOWED_TOOLS if tool not in granted]
        if missing:
            agent.allowed_tools = ",".join(granted + missing)
        # The model name comes from GEMINI_MODEL, so Gemini agents follow it.
        if agent.provider == "gemini":
            agent.model = get_settings().gemini_model
        # Unmodified prompts follow the current default for the agent's mode, so
        # prompt improvements reach agents created earlier. Hand-edited prompts stay.
        if is_default_instruction(agent.system_instruction):
            agent.system_instruction = system_instruction_for_mode(agent.mode)
    session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_product_url_column(engine)
    _ensure_agent_turn_columns(engine)
    _ensure_checkout_and_attachment_columns(engine)
    session = get_session_factory()()
    try:
        seed_database(session)
        _grant_default_tools(session)
        demo_agent = session.get(entities.AgentInstance, DEMO_AGENT_ID)
        if demo_agent is not None:
            demo_agent.display_name = "Alex"
            # Follow AGENT_PROVIDER from .env (gemini needs a key; otherwise mock).
            settings = get_settings()
            demo_agent.provider = settings.effective_provider
            demo_agent.model = (
                settings.gemini_model
                if settings.effective_provider == "gemini"
                else "mock-deterministic"
            )
            # Unmodified prompts follow the mode (vulnerable / patched default).
            if is_default_instruction(demo_agent.system_instruction):
                demo_agent.system_instruction = system_instruction_for_mode(demo_agent.mode)
            reset_agent(session, demo_agent)
    finally:
        session.close()
    yield


app = FastAPI(
    title="Nozama AI Shopping Assistant",
    description="Educational simulation of indirect prompt injection in a shopping agent.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(control.router)

"""
IMG_DIR = Path(__file__).resolve().parent.parent / "img"   # backend/img
app.mount("../../frontend/public/img", StaticFiles(directory=IMG_DIR), name="img")
"""


@app.get("/api/health")
def health():
    return {"ok": True, "service": "nozama-backend"}
