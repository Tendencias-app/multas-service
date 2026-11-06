from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.models import TipoMulta


@dataclass(frozen=True)
class PoliticaMulta:
    porcentaje_retraso_dia: float
    porcentaje_danos: float

    def calcular(self, tipo: TipoMulta, valor_alquiler: float, dias_retraso: int | None) -> float:
        if tipo is TipoMulta.RETRASO:
            if not dias_retraso or dias_retraso < 1:
                raise ValueError("Una multa por RETRASO requiere diasRetraso >= 1")
            valor = valor_alquiler * self.porcentaje_retraso_dia * dias_retraso
        else:
            valor = valor_alquiler * self.porcentaje_danos
        return round(valor, 2)

ZONA_NEGOCIO = ZoneInfo("America/Bogota")


def dias_de_retraso(fecha_fin: datetime, fecha_devolucion: datetime) -> int:
    """Días de calendario entre la fecha límite y la devolución, en hora de Bogotá."""
    limite = fecha_fin.astimezone(ZONA_NEGOCIO).date()
    entrega = fecha_devolucion.astimezone(ZONA_NEGOCIO).date()
    return max((entrega - limite).days, 0)