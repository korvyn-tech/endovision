"""Ponto de entrada da aplicação FastAPI do EndoVision."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from endovision import __version__
from endovision.api.routes import router as core_router
from endovision.api.routers import auth_router, billing_router
from endovision.api.schemas import HealthResponse
from endovision.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa banco de dados SQLite / SQLAlchemy
    init_db()
    yield


app = FastAPI(
    title="EndoVision API",
    description="Motor de Visão Computacional e Aprimoramento de Radiografias para Endodontia (Korvyn)",
    version=__version__,
    lifespan=lifespan,
)

# Configuração de CORS permissivo para uso local e integração web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint de saúde
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app="EndoVision",
        version=__version__,
    )

# Roteadores de processamento, autenticação e cobrança
app.include_router(core_router)
app.include_router(auth_router)
app.include_router(billing_router)

# Monta diretório estático do frontend se existir
# main.py -> api -> endovision -> src -> backend -> endovision_root (5 níveis acima)
static_dir = Path(__file__).resolve().parents[4] / "frontend" / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
