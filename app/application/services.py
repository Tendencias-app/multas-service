from uuid import UUID

from app.application.ports import MultaRepository
from app.domain.errors import MultaNoEncontrada
from app.domain.models import Multa


class MultaService:
    def __init__(self, repo: MultaRepository):
        self.repo = repo

    def crear(self, multa: Multa) -> Multa:
        return self.repo.guardar(multa)

    def obtener(self, multa_id: UUID) -> Multa:
        multa = self.repo.obtener(multa_id)
        if multa is None:
            raise MultaNoEncontrada(str(multa_id))
        return multa

    def listar_por_usuario(self, usuario_id: UUID) -> list[Multa]:
        return self.repo.listar_por_usuario(usuario_id)