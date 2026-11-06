# CarsATTM - Microservicio de Multas

Gestiona las multas por retraso o daños en los alquileres. Las multas se crean al recibir un evento de Kafka
desde Órdenes, y al pagarlas se publican eventos hacia Órdenes y Usuarios.

## Arquitectura

Hexagonal (puertos y adaptadores) en un único servicio desplegable.

| Capa | Ruta | Contenido |
|---|---|---|
| Dominio | `app/domain` | Entidad `Multa`, enums, cálculo de multas |
| Aplicación | `app/application` | Casos de uso (`MultaService`) y puertos |
| Entrada | `app/adapters/inbound` | API REST (FastAPI) y consumidor Kafka |
| Salida | `app/adapters/outbound` | PostgreSQL, productor Kafka, repositorio en memoria |

## Requisitos

- Python 3.12 o superior
- Docker Desktop
- (Opcional) minikube o kind y kubectl

## Ejecución local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
copy .env.example .env
docker compose up -d postgres kafka
uvicorn app.main:app --reload --port 8085
```

Crear los topics la primera vez:

```bash
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Multas_IniciarMulta
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Orden_MultaPagada
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Usuario_usuarioActivado
```

- Swagger: http://localhost:8085/docs
- Contrato OpenAPI: http://localhost:8085/openapi.json
- Salud: http://localhost:8085/health
- Métricas Prometheus: http://localhost:8085/metrics

## Todo en contenedores

```bash
docker compose --profile app up --build
```

## Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | vacío (memoria) | Cadena de conexión a PostgreSQL |
| `KAFKA_ENABLED` | `false` | Activa consumidor y productor |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Servidores Kafka |
| `KAFKA_GROUP_ID` | `ms-multas` | Grupo de consumo |
| `TOPIC_CREAR_MULTA` | `Multas_IniciarMulta` | Topic de entrada |
| `TOPIC_ORDEN_MULTA_PAGADA` | `Orden_MultaPagada` | Topic de salida a Órdenes |
| `TOPIC_USUARIO_ACTIVADO` | `Usuario_usuarioActivado` | Topic de salida a Usuarios |
| `PORCENTAJE_MULTA_RETRASO_DIA` | `0.10` | Porcentaje del total por día de retraso |
| `PORCENTAJE_MULTA_DANOS` | `0.30` | Porcentaje del total por daños |
| `LOG_LEVEL` | `INFO` | Nivel de logs |

## API REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/multas/{multaId}` | Consulta una multa |
| GET | `/api/v1/multas/usuarios/{usuarioId}` | Multas de un usuario |
| GET | `/api/v1/multas/ordenes/{ordenId}` | Multas de una orden |
| POST | `/api/v1/multas/{multaId}/pago` | Registra el pago y publica los eventos de salida |

## Eventos

### Entrada: `Multas_IniciarMulta` (desde Órdenes)

```json
{
  "ordenId": 15,
  "usuarioId": 1001,
  "tipo": "RETRASO",
  "valorAlquiler": 500000.0,
  "diasRetraso": 3,
  "observacion": "Devolución 3 días tarde"
}
```

- `tipo`: `RETRASO` o `DAÑOS`.
- `valorAlquiler`: total del carrito.
- `diasRetraso`: obligatorio y mayor o igual a 1 solo si el tipo es `RETRASO`. Se cuenta por cambio de día de calendario, en hora de Bogotá.
- Clave del mensaje: `ordenId`.
- Una orden tiene como máximo una multa por tipo. Un duplicado se ignora.

### Salida: `Orden_MultaPagada` (hacia Órdenes)

```json
{
  "multaId": 1,
  "ordenId": 15,
  "usuarioId": 1001,
  "precioMulta": 150000.0,
  "fechaPago": "2026-11-05T21:00:00+00:00"
}
```

### Salida: `Usuario_usuarioActivado` (hacia Usuarios)

```json
{
  "usuarioId": 1001,
  "multaId": 1,
  "fechaPago": "2026-11-05T21:00:00+00:00"
}
```

## Reglas de cálculo

- Retraso: `valorAlquiler × PORCENTAJE_MULTA_RETRASO_DIA × diasRetraso`
- Daños: `valorAlquiler × PORCENTAJE_MULTA_DANOS`

## Calidad y seguridad

```bash
ruff check .
pytest --cov=app
bandit -r app
pip-audit -r requirements.txt
```

El pipeline de CI (`.github/workflows/ci.yml`) ejecuta estas revisiones y construye la imagen.

## Kubernetes

Ver la carpeta `k8s/`. Las credenciales van en un `Secret` creado con `kubectl`, no en los archivos.

## Pendientes

- Confirmar con Órdenes el nombre final de los campos del evento de entrada.
- Confirmar los porcentajes de multa.
- Definir si `Usuario_usuarioActivado` se emite siempre o solo sin multas pendientes.
- Patrón outbox para evitar pérdida de eventos si Kafka falla tras guardar.