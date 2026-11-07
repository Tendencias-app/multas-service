from enum import Enum

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.inbound.http.schemas import ErrorResponse, MultaResponse
from app.application.services import MultaService
from app.domain.errors import MultaNoEncontrada, MultaYaPagada
from app.domain.models import EstadoMulta, Multa


class FiltroEstado(str, Enum):
    TODAS = "TODAS"
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"


router = APIRouter(prefix="/api/v1/multas", tags=["Multas"])


def get_service() -> MultaService:
    from app.main import service

    return service


def a_respuesta(m: Multa) -> MultaResponse:
    return MultaResponse(
        id=m.id, ordenId=m.orden_id, usuarioId=m.usuario_id, tipo=m.tipo,
        precioMulta=m.precio_multa, observacion=m.observacion, estado=m.estado,
        creadaEn=m.creada_en, fechaPago=m.fecha_pago,
    )


@router.get(
    "",
    response_model=list[MultaResponse],
    summary="Lista las multas filtradas por estado (por defecto, todas)",
)
def listar_multas(
    estado: FiltroEstado = FiltroEstado.TODAS,
    svc: MultaService = Depends(get_service),
):
    filtro = None if estado is FiltroEstado.TODAS else EstadoMulta(estado.value)
    return [a_respuesta(m) for m in svc.listar(filtro)]


@router.get("/usuarios/{usuario_id}", response_model=list[MultaResponse],
            responses={404: {"model": ErrorResponse}},
            summary="Lista las multas de un usuario")
def multas_de_usuario(usuario_id: int, svc: MultaService = Depends(get_service)):
    multas = svc.listar_por_usuario(usuario_id)
    if not multas:
        raise HTTPException(status_code=404, detail="El usuario no tiene multas")
    return [a_respuesta(m) for m in multas]


@router.get("/ordenes/{orden_id}", response_model=list[MultaResponse],
            responses={404: {"model": ErrorResponse}},
            summary="Lista las multas de una orden")
def multas_de_orden(orden_id: int, svc: MultaService = Depends(get_service)):
    multas = svc.listar_por_orden(orden_id)
    if not multas:
        raise HTTPException(status_code=404, detail="La orden no tiene multas")
    return [a_respuesta(m) for m in multas]


@router.get("/{multa_id}", response_model=MultaResponse,
            responses={404: {"model": ErrorResponse}},
            summary="Consulta una multa por ID")
def obtener_multa(multa_id: int, svc: MultaService = Depends(get_service)):
    try:
        return a_respuesta(svc.obtener(multa_id))
    except MultaNoEncontrada:
        raise HTTPException(status_code=404, detail="Multa no encontrada") from None


@router.post("/{multa_id}/pago", response_model=MultaResponse,
             responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
             summary="Registra el pago y publica los eventos de salida")
def pagar_multa(multa_id: int, svc: MultaService = Depends(get_service)):
    try:
        return a_respuesta(svc.pagar(multa_id))
    except MultaNoEncontrada:
        raise HTTPException(status_code=404, detail="Multa no encontrada") from None
    except MultaYaPagada:
        raise HTTPException(status_code=409, detail="La multa ya fue pagada") from None