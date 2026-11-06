from app.application.ports import EventPublisher, MultaRepository
from app.domain.calculo import PoliticaMulta
from app.domain.errors import MultaNoEncontrada
from app.domain.models import Multa, TipoMulta


class MultaService:
    def __init__(
        self,
        repo: MultaRepository,
        publisher: EventPublisher,
        politica: PoliticaMulta,
        topic_orden_pagada: str,
        topic_usuario_activado: str,
    ):
        self.repo = repo
        self.publisher = publisher
        self.politica = politica
        self.topic_orden_pagada = topic_orden_pagada
        self.topic_usuario_activado = topic_usuario_activado

    def crear_desde_evento(
        self,
        orden_id: int,
        usuario_id: int,
        tipo: TipoMulta,
        valor_alquiler: float,
        dias_retraso: int | None,
        observacion: str,
    ) -> Multa:
        precio = self.politica.calcular(tipo, valor_alquiler, dias_retraso)
        multa = Multa(
            orden_id=orden_id,
            usuario_id=usuario_id,
            tipo=tipo,
            precio_multa=precio,
            observacion=observacion,
        )
        return self.repo.guardar(multa)

    def obtener(self, multa_id: int) -> Multa:
        multa = self.repo.obtener(multa_id)
        if multa is None:
            raise MultaNoEncontrada(str(multa_id))
        return multa

    def listar_por_usuario(self, usuario_id: int) -> list[Multa]:
        return self.repo.listar_por_usuario(usuario_id)

    def listar_por_orden(self, orden_id: int) -> list[Multa]:
        return self.repo.listar_por_orden(orden_id)

    def pagar(self, multa_id: int) -> Multa:
        multa = self.obtener(multa_id)
        multa.pagar()
        multa = self.repo.guardar(multa)
        fecha = multa.fecha_pago.isoformat()
        self.publisher.publicar(
            self.topic_orden_pagada,
            str(multa.orden_id),
            {
                "multaId": multa.id,
                "ordenId": multa.orden_id,
                "usuarioId": multa.usuario_id,
                "precioMulta": multa.precio_multa,
                "fechaPago": fecha,
            },
        )
        self.publisher.publicar(
            self.topic_usuario_activado,
            str(multa.usuario_id),
            {"usuarioId": multa.usuario_id, "multaId": multa.id, "fechaPago": fecha},
        )
        return multa