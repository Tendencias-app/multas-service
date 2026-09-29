from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.adapters.inbound.http.schemas import (
    ActualizarEstadoRequest,
    CalculoMultaRequest,
    CalculoMultaResponse,
    CrearMultaRequest,
    ErrorResponse,
    MultaResponse,
    NotificacionRetrasoRequest,
    NotificacionRetrasoResponse,
    RestriccionUsuarioResponse,
)
from app.application.services import MultaService
from app.domain.errors import MultaNoEncontrada
from app.domain.models import EstadoMulta, Multa

router = APIRouter(prefix="/api/v1/multas", tags=["Multas"])

RESP_501 = {501: {"model": ErrorResponse, "description": "Aún no implementado"}}


def get_service() -> MultaService:
    from app.main import service

    return service


def no_implementado() -> HTTPException:
    return HTTPException(status_code=501, detail="Endpoint aún no implementado")


def a_respuesta(m: Multa) -> MultaResponse:
    return MultaResponse(
        id=m.id, ordenId=m.orden_id, usuarioId=m.usuario_id,
        vehiculoId=m.vehiculo_id, tipo=m.tipo, valorMulta=m.valor_multa,
        motivo=m.motivo, estado=m.estado, creadaEn=m.creada_en,
    )


@router.post("/calculos", response_model=CalculoMultaResponse, responses=RESP_501,
             summary="Calcula una multa sin registrarla")
def calcular_multa(body: CalculoMultaRequest):
    raise no_implementado()


@router.post("/notificaciones/retrasos", response_model=NotificacionRetrasoResponse,
             status_code=201, responses=RESP_501,
             summary="Registra una alerta por incumplimiento de devolución")
def notificar_retraso(body: NotificacionRetrasoRequest):
    raise no_implementado()


@router.post("", response_model=MultaResponse, status_code=201,
             summary="Registra una multa")
def crear_multa(body: CrearMultaRequest, svc: MultaService = Depends(get_service)):
    multa = Multa(orden_id=body.ordenId, usuario_id=body.usuarioId,
                  vehiculo_id=body.vehiculoId, tipo=body.tipo,
                  valor_multa=body.valorMulta, motivo=body.motivo)
    return a_respuesta(svc.crear(multa))


@router.get("", response_model=list[MultaResponse], responses=RESP_501,
            summary="Lista multas con filtros opcionales")
def listar_multas(
    usuario_id: Annotated[UUID | None, Query(alias="usuarioId")] = None,
    orden_id: Annotated[UUID | None, Query(alias="ordenId")] = None,
    estado: Annotated[EstadoMulta | None, Query()] = None,
):
    raise no_implementado()


@router.get("/ordenes/{orden_id}", response_model=list[MultaResponse],
            responses=RESP_501, summary="Lista las multas de una orden")
def multas_de_orden(orden_id: UUID):
    raise no_implementado()


@router.get("/usuarios/{usuario_id}/restriccion",
            response_model=RestriccionUsuarioResponse, responses=RESP_501,
            summary="Indica si el usuario debe ser restringido")
def restriccion_de_usuario(usuario_id: UUID):
    raise no_implementado()


@router.get("/usuarios/{usuario_id}", response_model=list[MultaResponse],
            summary="Lista las multas de un usuario")
def multas_de_usuario(usuario_id: UUID, svc: MultaService = Depends(get_service)):
    return [a_respuesta(m) for m in svc.listar_por_usuario(usuario_id)]


@router.patch("/{multa_id}/estado", response_model=MultaResponse,
              responses=RESP_501, summary="Actualiza el estado de una multa")
def actualizar_estado(multa_id: UUID, body: ActualizarEstadoRequest):
    raise no_implementado()


@router.get("/{multa_id}", response_model=MultaResponse,
            responses={404: {"model": ErrorResponse}},
            summary="Consulta una multa por ID")
def obtener_multa(multa_id: UUID, svc: MultaService = Depends(get_service)):
    try:
        return a_respuesta(svc.obtener(multa_id))
    except MultaNoEncontrada:
        raise HTTPException(status_code=404, detail="Multa no encontrada") from None