from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class TipoMulta(str, Enum):
    RETRASO = "RETRASO"
    DANOS = "DANOS"
    INCUMPLIMIENTO_DEVOLUCION = "INCUMPLIMIENTO_DEVOLUCION"
    OTRA_NOVEDAD = "OTRA_NOVEDAD"


class EstadoMulta(str, Enum):
    PENDIENTE = "PENDIENTE"
    NOTIFICADA = "NOTIFICADA"
    EN_REVISION = "EN_REVISION"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


@dataclass
class Multa:
    orden_id: UUID
    usuario_id: UUID
    vehiculo_id: UUID
    tipo: TipoMulta
    valor_multa: float
    motivo: str
    estado: EstadoMulta = EstadoMulta.PENDIENTE
    id: UUID = field(default_factory=uuid4)
    creada_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))