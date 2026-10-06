"""FastAPI entrypoint for the Nozama AI Shopping Assistant.

The browser talks only to this process. Gemini is an optional provider behind
AgentProvider; it never receives a cart object to mutate directly.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api import agents, cart, checkout, control, products
from app.database import Base, get_engine, get_session_factory
from app.models import entities  # noqa: F401  — register metadata
from app.seed import seed_database
from app.services.agents import reset_agent
from app.services.constants import DEMO_AGENT_ID

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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_product_url_column(engine)
    session = get_session_factory()()
    try:
        seed_database(session)
        demo_agent = session.get(entities.AgentInstance, DEMO_AGENT_ID)
        if demo_agent is not None:
            demo_agent.display_name = "Alex"
            demo_agent.system_instruction = (demo_agent.system_instruction or "").replace(
                "You are Nozi, the Nozama shopping assistant.",
                "You are Alex, the Nozama shopping assistant.",
                1,
            )
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
