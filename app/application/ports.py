from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models import Multa


class MultaRepository(ABC):
    @abstractmethod
    def guardar(self, multa: Multa) -> Multa: ...

    @abstractmethod
    def obtener(self, multa_id: UUID) -> Multa | None: ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: UUID) -> list[Multa]: ...