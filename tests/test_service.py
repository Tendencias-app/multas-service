from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.outbound.memory_repository import MemoryMultaRepository
from app.application.ports import EventPublisher
from app.application.services import MultaService
from app.domain.calculo import PoliticaMulta, dias_de_retraso
from app.domain.errors import MultaDuplicada, MultaYaPagada
from app.domain.models import EstadoMulta, TipoMulta


class FakePublisher(EventPublisher):
    def __init__(self):
        self.eventos = []

    def publicar(self, topic, key, payload):
        self.eventos.append((topic, key, payload))


def crear_servicio():
    publisher = FakePublisher()
    service = MultaService(
        MemoryMultaRepository(), publisher, PoliticaMulta(0.10, 0.30),
        "Orden_MultaPagada", "Usuario_usuarioActivado",
    )
    return service, publisher


def nueva_multa(service, tipo=TipoMulta.RETRASO, orden_id=1, dias=3):
    return service.crear_desde_evento(orden_id, 1001, tipo, 500000, dias, "prueba")


def test_multa_por_retraso_calcula_porcentaje_por_dia():
    service, _ = crear_servicio()
    assert nueva_multa(service).precio_multa == 150000


def test_multa_por_danos_aplica_porcentaje_fijo():
    service, _ = crear_servicio()
    assert nueva_multa(service, TipoMulta.DANOS, dias=None).precio_multa == 150000


def test_retraso_sin_dias_es_invalido():
    service, _ = crear_servicio()
    with pytest.raises(ValueError):
        nueva_multa(service, dias=None)


def test_multa_duplicada_se_rechaza():
    service, _ = crear_servicio()
    nueva_multa(service)
    with pytest.raises(MultaDuplicada):
        nueva_multa(service)


def test_pagar_publica_los_dos_eventos():
    service, publisher = crear_servicio()
    multa = service.pagar(nueva_multa(service).id)
    assert multa.estado is EstadoMulta.PAGADA
    assert multa.fecha_pago is not None
    assert [e[0] for e in publisher.eventos] == ["Orden_MultaPagada", "Usuario_usuarioActivado"]


def test_pagar_dos_veces_falla():
    service, _ = crear_servicio()
    multa = nueva_multa(service)
    service.pagar(multa.id)
    with pytest.raises(MultaYaPagada):
        service.pagar(multa.id)

BOGOTA = timezone(timedelta(hours=-5))


def test_entrega_al_dia_siguiente_es_un_dia_de_retraso():
    fin = datetime(2026, 11, 15, 20, 0, tzinfo=BOGOTA)
    devolucion = datetime(2026, 11, 16, 8, 0, tzinfo=BOGOTA)
    assert dias_de_retraso(fin, devolucion) == 1


def test_mismo_dia_aunque_sea_tarde_no_tiene_retraso():
    fin = datetime(2026, 11, 15, 8, 0, tzinfo=BOGOTA)
    devolucion = datetime(2026, 11, 15, 23, 59, tzinfo=BOGOTA)
    assert dias_de_retraso(fin, devolucion) == 0


def test_la_zona_horaria_no_inventa_un_dia():
    fin = datetime(2026, 11, 15, 10, 0, tzinfo=BOGOTA)
    devolucion = datetime(2026, 11, 16, 2, 0, tzinfo=timezone.utc)  # 9:00 p. m. del 15 en Bogotá
    assert dias_de_retraso(fin, devolucion) == 0


def test_devolucion_anticipada_no_da_dias_negativos():
    fin = datetime(2026, 11, 15, 10, 0, tzinfo=BOGOTA)
    devolucion = datetime(2026, 11, 14, 10, 0, tzinfo=BOGOTA)
    assert dias_de_retraso(fin, devolucion) == 0