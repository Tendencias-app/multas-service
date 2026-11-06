import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.adapters.inbound.http.routes import router
from app.adapters.inbound.kafka.consumer import CrearMultaConsumer
from app.adapters.outbound.kafka_publisher import KafkaEventPublisher
from app.adapters.outbound.memory_repository import MemoryMultaRepository
from app.adapters.outbound.noop_publisher import NoOpEventPublisher
from app.adapters.outbound.postgres.database import Base, crear_engine, crear_session_factory
from app.adapters.outbound.postgres.repository import PostgresMultaRepository
from app.application.services import MultaService
from app.config import settings
from app.domain.calculo import PoliticaMulta

logging.basicConfig(
    level=settings.log_level,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)

engine = None
if settings.database_url:
    engine = crear_engine(settings.database_url)
    repo = PostgresMultaRepository(crear_session_factory(engine))
else:
    repo = MemoryMultaRepository()

if settings.kafka_enabled:
    publisher = KafkaEventPublisher(settings.kafka_bootstrap_servers)
else:
    publisher = NoOpEventPublisher()

service = MultaService(
    repo=repo,
    publisher=publisher,
    politica=PoliticaMulta(
        settings.porcentaje_multa_retraso_dia, settings.porcentaje_multa_danos
    ),
    topic_orden_pagada=settings.topic_orden_multa_pagada,
    topic_usuario_activado=settings.topic_usuario_activado,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if engine is not None:
        Base.metadata.create_all(engine)
    consumer = None
    if settings.kafka_enabled:
        consumer = CrearMultaConsumer(
            settings.kafka_bootstrap_servers,
            settings.kafka_group_id,
            settings.topic_crear_multa,
            service,
        )
        consumer.iniciar()
    yield
    if consumer is not None:
        consumer.detener()
    publisher.cerrar()
    if engine is not None:
        engine.dispose()


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan,
              description="Gestión de multas por incumplimientos en alquileres.")
app.include_router(router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Operación"])
def health():
    return {"status": "ok"}