from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_crear_y_consultar_multa():
    body = {"ordenId": str(uuid4()), "usuarioId": str(uuid4()),
            "vehiculoId": str(uuid4()), "tipo": "RETRASO",
            "valorMulta": 90000, "motivo": "Devolución tardía"}
    creada = client.post("/api/v1/multas", json=body)
    assert creada.status_code == 201
    consulta = client.get(f"/api/v1/multas/{creada.json()['id']}")
    assert consulta.status_code == 200


def test_multa_inexistente_da_404():
    assert client.get(f"/api/v1/multas/{uuid4()}").status_code == 404

def test_listar_multas_de_usuario():
    usuario = str(uuid4())
    body = {"ordenId": str(uuid4()), "usuarioId": usuario,
            "vehiculoId": str(uuid4()), "tipo": "RETRASO",
            "valorMulta": 50000, "motivo": "Retraso de dos horas"}
    client.post("/api/v1/multas", json=body)
    resp = client.get(f"/api/v1/multas/usuarios/{usuario}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1



UUID_X = "11111111-1111-1111-1111-111111111111"
CALCULO_BODY = {
    "ordenId": UUID_X, "usuarioId": UUID_X, "vehiculoId": UUID_X,
    "fechaLimiteDevolucion": "2026-10-05T10:00:00Z",
    "fechaDevolucionReal": "2026-10-06T14:30:00Z",
    "tarifaDiaria": 180000, "tipoIncumplimiento": "RETRASO",
}
NOTIF_BODY = {
    "ordenId": UUID_X, "usuarioId": UUID_X, "vehiculoId": UUID_X,
    "fechaLimiteDevolucion": "2026-10-05T10:00:00Z", "horasRetraso": 28,
}


@pytest.mark.parametrize("metodo,ruta,body", [
    ("post", "/api/v1/multas/calculos", CALCULO_BODY),
    ("post", "/api/v1/multas/notificaciones/retrasos", NOTIF_BODY),
    ("get", "/api/v1/multas", None),
    ("get", f"/api/v1/multas/ordenes/{UUID_X}", None),
    ("get", f"/api/v1/multas/usuarios/{UUID_X}/restriccion", None),
    ("patch", f"/api/v1/multas/{UUID_X}/estado", {"estado": "NOTIFICADA"}),
])
def test_endpoints_pendientes_devuelven_501(metodo, ruta, body):
    resp = getattr(client, metodo)(ruta, json=body) if body else getattr(client, metodo)(ruta)
    assert resp.status_code == 501