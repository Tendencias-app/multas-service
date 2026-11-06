from app.application.ports import MultaRepository
from app.domain.errors import MultaDuplicada
from app.domain.models import Multa


class MemoryMultaRepository(MultaRepository):
    def __init__(self):
        self._datos: dict[int, Multa] = {}
        self._siguiente_id = 1

    def guardar(self, multa: Multa) -> Multa:
        if multa.id is None:
            if any(
                m.orden_id == multa.orden_id and m.tipo == multa.tipo
                for m in self._datos.values()
            ):
                raise MultaDuplicada(f"{multa.orden_id}/{multa.tipo.value}")
            multa.id = self._siguiente_id
            self._siguiente_id += 1
        self._datos[multa.id] = multa
        return multa

    def obtener(self, multa_id: int) -> Multa | None:
        return self._datos.get(multa_id)

    def listar_por_usuario(self, usuario_id: int) -> list[Multa]:
        return [m for m in self._datos.values() if m.usuario_id == usuario_id]

    def listar_por_orden(self, orden_id: int) -> list[Multa]:
        return [m for m in self._datos.values() if m.orden_id == orden_id]