import json
import logging
import threading

from confluent_kafka import Consumer
from pydantic import ValidationError

from app.adapters.inbound.kafka.events import CrearMultaEvento
from app.application.services import MultaService
from app.domain.errors import MultaDuplicada

log = logging.getLogger(__name__)


class CrearMultaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str, topic: str, service: MultaService):
        self._config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        self._topic = topic
        self._service = service
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="kafka-crear-multa", daemon=True)

    def iniciar(self) -> None:
        self._thread.start()

    def detener(self) -> None:
        self._stop.set()
        self._thread.join(timeout=10)

    def _loop(self) -> None:
        consumer = Consumer(self._config)
        consumer.subscribe([self._topic])
        log.info("Consumidor suscrito a %s", self._topic)
        try:
            while not self._stop.is_set():
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    log.warning("Error de Kafka: %s", msg.error())
                    continue
                if self._procesar(msg.value()):
                    consumer.commit(message=msg, asynchronous=False)
        finally:
            consumer.close()

    def _procesar(self, valor: bytes) -> bool:
        try:
            evento = CrearMultaEvento(**json.loads(valor))
            multa = self._service.crear_desde_evento(
                orden_id=evento.ordenId,
                usuario_id=evento.usuarioId,
                tipo=evento.tipo,
                valor_alquiler=evento.valorAlquiler,
                dias_retraso=evento.diasRetraso,
                observacion=evento.observacion,
            )
            log.info("Multa %s creada para la orden %s", multa.id, multa.orden_id)
            return True
        except (ValueError, TypeError, ValidationError):
            log.error("Mensaje inválido descartado: %r", valor)
            return True
        except MultaDuplicada:
            log.warning("Multa duplicada ignorada: %r", valor)
            return True
        except Exception:
            log.exception("Error procesando el mensaje; no se confirma el offset")
            return False