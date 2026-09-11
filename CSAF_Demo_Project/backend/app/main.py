"""FastAPI entrypoint for the Nozama AI Shopping Assistant.

The browser talks only to this process. Gemini is an optional provider behind
AgentProvider; it never receives a cart object to mutate directly.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, cart, checkout, control, products
from app.database import Base, get_engine, get_session_factory
from app.models import entities  # noqa: F401  — register metadata
from app.seed import seed_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    session = get_session_factory()()
    try:
        seed_database(session)
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


@app.get("/api/health")
def health():
    return {"ok": True, "service": "nozama-backend"}
