"""Ponto de entrada da aplicação FastAPI do EndoVision."""

from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from endovision import __version__
from endovision.api.routes import router
from endovision.api.schemas import HealthResponse

app = FastAPI(
    title="EndoVision API",
    description="Motor de Visão Computacional e Aprimoramento de Radiografias para Endodontia (Corvin)",
    version=__version__,
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

# Roteador principal de endpoints de processamento
app.include_router(router)

# Monta diretório estático do frontend se existir
# main.py -> api -> endovision -> src -> backend -> endovision_root (5 níveis acima)
static_dir = Path(__file__).resolve().parents[4] / "frontend" / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
