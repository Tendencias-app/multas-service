from abc import ABC, abstractmethod

from app.domain.models import Multa


class MultaRepository(ABC):
    @abstractmethod
    def guardar(self, multa: Multa) -> Multa: ...

    @abstractmethod
    def obtener(self, multa_id: int) -> Multa | None: ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int) -> list[Multa]: ...

    @abstractmethod
    def listar_por_orden(self, orden_id: int) -> list[Multa]: ...


class EventPublisher(ABC):
    @abstractmethod
    def publicar(self, topic: str, key: str, payload: dict) -> None: ...

    def cerrar(self) -> None:
        return None