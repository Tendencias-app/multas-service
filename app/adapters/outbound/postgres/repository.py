from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, UniqueConstraint, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from app.adapters.outbound.postgres.database import Base
from app.application.ports import MultaRepository
from app.domain.errors import MultaDuplicada, MultaNoEncontrada
from app.domain.models import EstadoMulta, Multa, TipoMulta


class MultaORM(Base):
    __tablename__ = "multas"
    __table_args__ = (UniqueConstraint("orden_id", "tipo", name="uq_multa_orden_tipo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orden_id: Mapped[int] = mapped_column(Integer, index=True)
    usuario_id: Mapped[int] = mapped_column(BigInteger, index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    precio_multa: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False))
    observacion: Mapped[str] = mapped_column(String(500), default="")
    estado: Mapped[str] = mapped_column(String(20))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def a_dominio(f: MultaORM) -> Multa:
    return Multa(
        id=f.id, orden_id=f.orden_id, usuario_id=f.usuario_id, tipo=TipoMulta(f.tipo),
        precio_multa=f.precio_multa, observacion=f.observacion,
        estado=EstadoMulta(f.estado), creada_en=f.creada_en, fecha_pago=f.fecha_pago,
    )


class PostgresMultaRepository(MultaRepository):
    def __init__(self, session_factory: sessionmaker[Session]):
        self._sf = session_factory

    def guardar(self, multa: Multa) -> Multa:
        with self._sf() as session:
            try:
                if multa.id is None:
                    fila = MultaORM(
                        orden_id=multa.orden_id, usuario_id=multa.usuario_id,
                        tipo=multa.tipo.value, precio_multa=multa.precio_multa,
                        observacion=multa.observacion, estado=multa.estado.value,
                        creada_en=multa.creada_en, fecha_pago=multa.fecha_pago,
                    )
                    session.add(fila)
                else:
                    fila = session.get(MultaORM, multa.id)
                    if fila is None:
                        raise MultaNoEncontrada(str(multa.id))
                    fila.estado = multa.estado.value
                    fila.fecha_pago = multa.fecha_pago
                    fila.observacion = multa.observacion
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise MultaDuplicada(f"{multa.orden_id}/{multa.tipo.value}") from exc
            session.refresh(fila)
            return a_dominio(fila)

    def obtener(self, multa_id: int) -> Multa | None:
        with self._sf() as session:
            fila = session.get(MultaORM, multa_id)
            return a_dominio(fila) if fila else None

    def listar_por_usuario(self, usuario_id: int) -> list[Multa]:
        with self._sf() as session:
            q = select(MultaORM).where(MultaORM.usuario_id == usuario_id).order_by(MultaORM.id)
            return [a_dominio(f) for f in session.scalars(q).all()]

    def listar_por_orden(self, orden_id: int) -> list[Multa]:
        with self._sf() as session:
            q = select(MultaORM).where(MultaORM.orden_id == orden_id).order_by(MultaORM.id)
            return [a_dominio(f) for f in session.scalars(q).all()]