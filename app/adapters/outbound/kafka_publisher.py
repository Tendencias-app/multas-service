import json
import logging

from confluent_kafka import Producer

from app.application.ports import EventPublisher

log = logging.getLogger(__name__)


class KafkaEventPublisher(EventPublisher):
    def __init__(self, bootstrap_servers: str):
        self._producer = Producer({"bootstrap.servers": bootstrap_servers})

    def publicar(self, topic: str, key: str, payload: dict) -> None:
        self._producer.produce(
            topic,
            key=key.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            on_delivery=self._al_entregar,
        )
        pendientes = self._producer.flush(5)
        if pendientes:
            raise RuntimeError(f"No se pudo publicar en {topic}")

    @staticmethod
    def _al_entregar(err, msg) -> None:
        if err is not None:
            log.error("Fallo al entregar a %s: %s", msg.topic(), err)
        else:
            log.info("Evento entregado topic=%s partición=%s", msg.topic(), msg.partition())

    def cerrar(self) -> None:
        self._producer.flush(5)