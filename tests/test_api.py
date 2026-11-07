from itertools import count

from fastapi.testclient import TestClient

from app.domain.models import TipoMulta
from app.main import app, service

client = TestClient(app)
_ordenes = count(1000)


def crear_multa(usuario_id=1001):
    return service.crear_desde_evento(
        next(_ordenes), usuario_id, TipoMulta.RETRASO, 500000, 3, "prueba"
    )


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_consultar_multa_por_id():
    multa = crear_multa()
    resp = client.get(f"/api/v1/multas/{multa.id}")
    assert resp.status_code == 200
    assert resp.json()["precioMulta"] == 150000


def test_multa_inexistente_da_404():
    assert client.get("/api/v1/multas/999999").status_code == 404


def test_listar_por_usuario_y_por_orden():
    multa = crear_multa(usuario_id=777)
    por_usuario = client.get("/api/v1/multas/usuarios/777").json()
    por_orden = client.get(f"/api/v1/multas/ordenes/{multa.orden_id}").json()
    assert len(por_usuario) == 1
    assert por_orden[0]["id"] == multa.id

def test_listar_multas_por_estado():
    pendiente = crear_multa(888)
    pagada = crear_multa(888)
    client.post(f"/api/v1/multas/{pagada.id}/pago")

    def ids(estado=None):
        params = {"estado": estado} if estado else {}
        return {m["id"] for m in client.get("/api/v1/multas", params=params).json()}

    assert {pendiente.id, pagada.id} <= ids()
    assert pendiente.id in ids("PENDIENTE") and pagada.id not in ids("PENDIENTE")
    assert pagada.id in ids("PAGADA") and pendiente.id not in ids("PAGADA")
    assert client.get("/api/v1/multas", params={"estado": "XYZ"}).status_code == 422

def test_pagar_multa_y_no_permitir_segundo_pago():
    multa = crear_multa()
    ok = client.post(f"/api/v1/multas/{multa.id}/pago")
    assert ok.status_code == 200
    assert ok.json()["estado"] == "PAGADA"
    assert ok.json()["fechaPago"] is not None
    assert client.post(f"/api/v1/multas/{multa.id}/pago").status_code == 409


def test_pagar_multa_inexistente_da_404():
    assert client.post("/api/v1/multas/999999/pago").status_code == 404

def test_usuario_sin_multas_da_404():
    assert client.get("/api/v1/multas/usuarios/987654").status_code == 404

def test_orden_sin_multas_da_404():
    assert client.get("/api/v1/multas/ordenes/987654").status_code == 404