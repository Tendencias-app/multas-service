import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.adapters.inbound.http.routes import router
from app.adapters.outbound.memory_repository import MemoryMultaRepository
from app.application.services import MultaService
from app.config import settings

logging.basicConfig(
    level=settings.log_level,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)

service = MultaService(MemoryMultaRepository())

app = FastAPI(title=settings.app_name, version=settings.version,
              description="Gestión de multas por incumplimientos en alquileres.")
app.include_router(router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["Operación"])
def health():
    return {"status": "ok"}