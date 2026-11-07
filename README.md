# CarsATTM - Microservicio de Multas

Gestiona las multas por retraso o daños en los alquileres. Las multas se crean al recibir un evento de Kafka
desde Órdenes, y al pagarlas se publican eventos hacia Órdenes y Usuarios.

- Repositorio: https://github.com/Tendencias-app/multas-service
- Imagen Docker: `joricor/multas-service` (`1.0.3` y `latest`)

## Arquitectura

Hexagonal (puertos y adaptadores) en un único servicio desplegable.

| Capa | Ruta | Contenido |
|---|---|---|
| Dominio | `app/domain` | Entidad `Multa`, enums, cálculo de multas |
| Aplicación | `app/application` | Casos de uso (`MultaService`) y puertos |
| Entrada | `app/adapters/inbound` | API REST (FastAPI) y consumidor Kafka |
| Salida | `app/adapters/outbound` | PostgreSQL y productor Kafka |

## Requisitos

- Docker Desktop
- Para desarrollo: Python 3.12 o superior
- (Opcional) Kubernetes local (Docker Desktop, minikube o kind) y kubectl

## Prueba rápida con Docker Compose

Levanta PostgreSQL, el microservicio de multas, el front y, opcionalmente, un Kafka local. Cree una carpeta
que contenga solo el `docker-compose.yml` de este repositorio y ejecute dentro de ella:

```bash
docker compose pull
docker compose --profile local-kafka up -d
docker compose ps
```

- API de multas: http://localhost:8085/docs
- Front: http://localhost

El front usa la variable `Api__MultasBaseUrl=http://multas:8085`, que apunta al servicio de multas por su
nombre dentro de la red de Compose. `localhost` no sirve dentro de un contenedor.

El perfil `local-kafka` levanta un Kafka local. Si el equipo usa un Kafka compartido, omita el perfil y
defina antes la dirección:

```powershell
$env:COMPOSE_KAFKA_SERVERS="DIRECCION:9092"
docker compose up -d
```

Sin el perfil y sin esa variable, el servicio apunta a `kafka:29092`, que no existe, y no podrá conectarse.

Crear los topics la primera vez (solo con el Kafka local):

```bash
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Multas_IniciarMulta
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Orden_MultaPagada
docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Usuario_usuarioActivado
```

Enviar un evento de prueba (PowerShell):

```powershell
'{"ordenId":20,"usuarioId":1001,"tipo":"RETRASO","valorAlquiler":500000,"diasRetraso":3,"observacion":"Prueba"}' | docker exec -i kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic Multas_IniciarMulta
```

Consultar, pagar y ver los eventos de salida:

```powershell
Invoke-RestMethod "http://localhost:8085/api/v1/multas?estado=PENDIENTE"
Invoke-RestMethod -Method Post http://localhost:8085/api/v1/multas/1/pago
docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic Orden_MultaPagada --from-beginning --timeout-ms 5000
docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic Usuario_usuarioActivado --from-beginning --timeout-ms 5000
```

Apagar y borrar los datos:

```bash
docker compose --profile local-kafka down -v
```

## Kubernetes

Los manifiestos están en `k8s/` y despliegan Kafka, PostgreSQL, el microservicio de multas y el front en el
namespace activo (`default`, si no se cambió). Con el clúster activo:

```bash
kubectl apply -f k8s/
kubectl get pods
```

| Archivo | Contenido |
|---|---|
| `00-secret.yaml` | Secret `multas-db` con las credenciales de PostgreSQL |
| `kafka.yaml` | Deployment y Service de Kafka (`kafka:9092`) |
| `postgres.yaml` | Volumen, Deployment y Service de PostgreSQL |
| `multas.yaml` | ConfigMap, Deployment y Service `ms-multas` (puerto 8085) |
| `front.yaml` | ConfigMap, Deployment y Service `front` (LoadBalancer, puerto 80) |

El Secret contiene credenciales de prueba (`multas`/`multas`). No use esos valores fuera de desarrollo.

Dentro del clúster, el front llama a multas en `http://ms-multas:8085`. Los servicios se encuentran por
nombre, y solo funciona dentro del mismo namespace.

### Abrir el front

Depende del tipo de clúster:

- Docker Desktop en modo `kubeadm`: `http://localhost`
- minikube: `minikube service front --url`
- Cualquier clúster (por ejemplo Docker Desktop en modo `kind`): `kubectl port-forward svc/front 8080:80`
  y abrir `http://localhost:8080`

### Topics y eventos en Kubernetes

Los comandos son los mismos que con Compose, cambiando `docker exec` por `kubectl exec`:

```powershell
kubectl exec deploy/kafka -- /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Multas_IniciarMulta
kubectl exec deploy/kafka -- /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Orden_MultaPagada
kubectl exec deploy/kafka -- /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server localhost:9092 --topic Usuario_usuarioActivado
'{"ordenId":20,"usuarioId":1001,"tipo":"RETRASO","valorAlquiler":500000,"diasRetraso":3,"observacion":"Prueba k8s"}' | kubectl exec -i deploy/kafka -- /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic Multas_IniciarMulta
```

Para consultar la API desde la máquina: `kubectl port-forward svc/ms-multas 8085:8085`.

Borrar todo lo desplegado (incluye los datos de PostgreSQL): `kubectl delete -f k8s/`.

## Desarrollo local

El servicio corre en la máquina y usa dos contenedores de apoyo: PostgreSQL (con el puerto 5432 publicado)
y el Kafka del compose.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
copy .env.example .env
docker run -d --name multas-pg -e POSTGRES_USER=multas -e POSTGRES_PASSWORD=multas -e POSTGRES_DB=multas_db -p 5432:5432 postgres:16-alpine
docker compose --profile local-kafka up -d kafka
uvicorn app.main:app --reload --port 8085
```

El archivo `.env.example` contiene:
- DATABASE_URL=postgresql+psycopg://multas:multas@localhost:5432/multas_db
- KAFKA_ENABLED=true
- KAFKA_BOOTSTRAP_SERVERS=localhost:9092


Para borrar la base de desarrollo: `docker rm -f multas-pg`.

- Swagger: http://localhost:8085/docs
- Contrato OpenAPI: http://localhost:8085/openapi.json
- Salud: http://localhost:8085/health
- Métricas Prometheus: http://localhost:8085/metrics

Construir y publicar la imagen:

```bash
docker build -t joricor/multas-service:1.0.3 -t joricor/multas-service:latest .
docker push joricor/multas-service:1.0.3
docker push joricor/multas-service:latest
```

## Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | vacío | Cadena de conexión a PostgreSQL |
| `KAFKA_ENABLED` | `false` | Activa consumidor y productor |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Servidores Kafka |
| `KAFKA_GROUP_ID` | `ms-multas` | Grupo de consumo |
| `TOPIC_CREAR_MULTA` | `Multas_IniciarMulta` | Topic de entrada |
| `TOPIC_ORDEN_MULTA_PAGADA` | `Orden_MultaPagada` | Topic de salida a Órdenes |
| `TOPIC_USUARIO_ACTIVADO` | `Usuario_usuarioActivado` | Topic de salida a Usuarios |
| `PORCENTAJE_MULTA_RETRASO_DIA` | `0.10` | Porcentaje del valor del alquiler por día de retraso |
| `PORCENTAJE_MULTA_DANOS` | `0.30` | Porcentaje del valor del alquiler por daños |
| `LOG_LEVEL` | `INFO` | Nivel de logs |

En el compose, la dirección de Kafka del contenedor se define con la variable `COMPOSE_KAFKA_SERVERS`
(por defecto `kafka:29092`).

## API REST

| Método | Ruta | Respuestas | Descripción |
|---|---|---|---|
| GET | `/api/v1/multas?estado=` | 200 | Lista las multas; `estado` puede ser `TODAS` (por defecto), `PENDIENTE` o `PAGADA` |
| GET | `/api/v1/multas/{multaId}` | 200, 404 | Consulta una multa |
| GET | `/api/v1/multas/usuarios/{usuarioId}` | 200, 404 | Multas de un usuario; 404 si no tiene ninguna |
| GET | `/api/v1/multas/ordenes/{ordenId}` | 200, 404 | Multas de una orden; 404 si no tiene ninguna |
| POST | `/api/v1/multas/{multaId}/pago` | 200, 404, 409 | Registra el pago y publica los eventos de salida; 409 si ya estaba pagada |

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

- `tipo`: `RETRASO` o `DANOS`.
- `valorAlquiler`: total del carrito; debe ser mayor que 0.
- `diasRetraso`: obligatorio y mayor o igual a 1 solo si el tipo es `RETRASO`.
- `observacion`: opcional, máximo 500 caracteres.
- Clave del mensaje: `ordenId`.
- Una orden tiene como máximo una multa por tipo. Un duplicado se ignora.
- Un mensaje inválido se descarta y se registra en el log.

### Salida: `Orden_MultaPagada` (hacia Órdenes)

Clave del mensaje: `ordenId`.

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

Clave del mensaje: `usuarioId`. Se emite en cada pago de multa, aunque el usuario tenga otras pendientes.

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
- Los días de retraso se cuentan por cambio de día de calendario, en hora de Bogotá.

## Calidad y seguridad

```bash
ruff check .
pytest --cov=app
bandit -r app
pip-audit -r requirements.txt
```

El pipeline de CI (`.github/workflows/ci.yml`) ejecuta estas revisiones y construye la imagen.

## Pendientes

- Acordar con el equipo el Kafka compartido y los nombres finales de los topics.
- Patrón outbox para evitar pérdida de eventos si Kafka falla tras guardar.