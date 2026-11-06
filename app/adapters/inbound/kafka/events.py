from pydantic import BaseModel, Field, model_validator

from app.domain.models import TipoMulta


class CrearMultaEvento(BaseModel):
    ordenId: int
    usuarioId: int
    tipo: TipoMulta
    valorAlquiler: float = Field(gt=0)
    diasRetraso: int | None = Field(default=None, ge=1)
    observacion: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def exigir_dias_si_retraso(self):
        if self.tipo is TipoMulta.RETRASO and self.diasRetraso is None:
            raise ValueError("diasRetraso es obligatorio para RETRASO")
        return self