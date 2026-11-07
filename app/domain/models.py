from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from app.domain.errors import MultaYaPagada


class TipoMulta(str, Enum):
    RETRASO = "RETRASO"
    DANOS = "DANOS"


class EstadoMulta(str, Enum):
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"


@dataclass
class Multa:
    orden_id: int
    usuario_id: int
    tipo: TipoMulta
    precio_multa: float
    observacion: str
    estado: EstadoMulta = EstadoMulta.PENDIENTE
    id: int | None = None
    creada_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fecha_pago: datetime | None = None

    def pagar(self) -> None:
        if self.estado is EstadoMulta.PAGADA:
            raise MultaYaPagada(str(self.id))
        self.estado = EstadoMulta.PAGADA
        self.fecha_pago = datetime.now(timezone.utc)