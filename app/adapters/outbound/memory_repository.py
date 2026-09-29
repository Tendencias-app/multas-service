from uuid import UUID

from app.application.ports import MultaRepository
from app.domain.models import Multa


class MemoryMultaRepository(MultaRepository):
    def __init__(self):
        self._datos: dict[UUID, Multa] = {}

    def guardar(self, multa: Multa) -> Multa:
        self._datos[multa.id] = multa
        return multa

    def obtener(self, multa_id: UUID) -> Multa | None:
        return self._datos.get(multa_id)

    def listar_por_usuario(self, usuario_id: UUID) -> list[Multa]:
        return [m for m in self._datos.values() if m.usuario_id == usuario_id]