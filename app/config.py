from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CarsATTM - Microservicio de Multas"
    version: str = "1.0.0"
    log_level: str = "INFO"


settings = Settings()