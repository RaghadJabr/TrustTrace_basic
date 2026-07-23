from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import assessments, health, jofs
from .core.errors import register_exception_handlers
from .db.seed import seed_demo_data
from .db.session import SessionLocal
from .integrations.open_finance.provider import JOFSAdapter
from .ml.traditional.service import TraditionalFraudModelService
from .services.web3_rules_service import Web3RuleEngine

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.jofs = JOFSAdapter()
    app.state.web3_engine = Web3RuleEngine()
    app.state.traditional_model_service = TraditionalFraudModelService()

    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="TrustTrace Prototype API",
    version="0.2.0",
    description=(
        "Explainable pre-authorization fraud assessment for traditional and "
        "Web3 payments. The traditional flow is backed by a trained LightGBM "
        "model with SHAP explanations, persisted to PostgreSQL."
    ),
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(jofs.router)
app.include_router(assessments.router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")
