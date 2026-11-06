import logging

from app.application.ports import EventPublisher

log = logging.getLogger(__name__)


class NoOpEventPublisher(EventPublisher):
    def publicar(self, topic: str, key: str, payload: dict) -> None:
        log.info("Evento (sin Kafka) topic=%s key=%s payload=%s", topic, key, payload)