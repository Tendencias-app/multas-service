from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models import EstadoMulta, TipoMulta


class CrearMultaRequest(BaseModel):
    ordenId: UUID
    usuarioId: UUID
    vehiculoId: UUID
    tipo: TipoMulta
    valorMulta: float = Field(ge=0, examples=[90000])
    motivo: str = Field(min_length=5, max_length=500)


class MultaResponse(BaseModel):
    id: UUID
    ordenId: UUID
    usuarioId: UUID
    vehiculoId: UUID
    tipo: TipoMulta
    valorMulta: float
    motivo: str
    estado: EstadoMulta
    creadaEn: datetime


class CalculoMultaRequest(BaseModel):
    ordenId: UUID
    usuarioId: UUID
    vehiculoId: UUID
    fechaLimiteDevolucion: datetime
    fechaDevolucionReal: datetime | None = None
    tarifaDiaria: float = Field(ge=0, examples=[180000])
    tipoIncumplimiento: TipoMulta


class CalculoMultaResponse(BaseModel):
    ordenId: UUID
    usuarioId: UUID
    tipo: TipoMulta
    horasRetraso: int = Field(ge=0)
    valorBase: float
    valorMulta: float
    moneda: str = "COP"
    requiereBloqueo: bool
    motivo: str


class ActualizarEstadoRequest(BaseModel):
    estado: EstadoMulta
    observaciones: str | None = Field(default=None, max_length=500)


class RestriccionUsuarioResponse(BaseModel):
    usuarioId: UUID
    restringido: bool
    motivo: str | None = None
    multasPendientes: int = Field(ge=0)
    multaIds: list[UUID] = []


class NotificacionRetrasoRequest(BaseModel):
    ordenId: UUID
    usuarioId: UUID
    vehiculoId: UUID
    fechaLimiteDevolucion: datetime
    horasRetraso: int = Field(ge=0)


class NotificacionRetrasoResponse(BaseModel):
    id: UUID
    ordenId: UUID
    usuarioId: UUID
    horasRetraso: int
    mensaje: str
    creadaEn: datetime


class ErrorResponse(BaseModel):
    codigo: str
    mensaje: str