from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CarsATTM - Microservicio de Multas"
    version: str = "1.0.0"
    log_level: str = "INFO"

    database_url: str | None = None

    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "ms-multas"
    topic_crear_multa: str = "Multas_IniciarMulta"
    topic_orden_multa_pagada: str = "Orden_MultaPagada"
    topic_usuario_activado: str = "Usuario_usuarioActivado"

    porcentaje_multa_retraso_dia: float = 0.10
    porcentaje_multa_danos: float = 0.30


settings = Settings()