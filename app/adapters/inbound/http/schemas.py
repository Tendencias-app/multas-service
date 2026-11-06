from datetime import datetime

from pydantic import BaseModel

from app.domain.models import EstadoMulta, TipoMulta


class MultaResponse(BaseModel):
    id: int
    ordenId: int
    usuarioId: int
    tipo: TipoMulta
    precioMulta: float
    observacion: str
    estado: EstadoMulta
    creadaEn: datetime
    fechaPago: datetime | None = None


class ErrorResponse(BaseModel):
    codigo: str
    mensaje: str