from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Proceso(Base):
    __tablename__ = "procesos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_necesidad: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    nombre_entidad: Mapped[str | None] = mapped_column(String)
    tipo_necesidad: Mapped[str | None] = mapped_column(String)
    estado_necesidad: Mapped[str | None] = mapped_column(String)
    fecha_publicacion: Mapped[date | None] = mapped_column(Date)
    fecha_limite: Mapped[date | None] = mapped_column(Date)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    funcionario: Mapped[Funcionario | None] = relationship(
        back_populates="proceso",
        cascade="all, delete-orphan",
        uselist=False,
    )
    lugar_entrega: Mapped[LugarEntrega | None] = relationship(
        back_populates="proceso",
        cascade="all, delete-orphan",
        uselist=False,
    )
    items_compra: Mapped[list[ItemCompra]] = relationship(
        back_populates="proceso",
        cascade="all, delete-orphan",
    )


class Funcionario(Base):
    __tablename__ = "funcionarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False, unique=True)
    nombre: Mapped[str | None] = mapped_column(String)
    correo: Mapped[str | None] = mapped_column(String)

    proceso: Mapped[Proceso] = relationship(back_populates="funcionario")


class LugarEntrega(Base):
    __tablename__ = "lugares_entrega"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False, unique=True)
    provincia: Mapped[str | None] = mapped_column(String)
    canton: Mapped[str | None] = mapped_column(String)
    parroquia: Mapped[str | None] = mapped_column(String)
    direccion: Mapped[str | None] = mapped_column(Text)

    proceso: Mapped[Proceso] = relationship(back_populates="lugar_entrega")


class ItemCompra(Base):
    __tablename__ = "items_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False)
    numero: Mapped[int | None] = mapped_column(Integer)
    cpc: Mapped[str | None] = mapped_column(String)
    unidad: Mapped[str | None] = mapped_column(String)
    cantidad: Mapped[Decimal | None] = mapped_column(Numeric)

    proceso: Mapped[Proceso] = relationship(back_populates="items_compra")


class EjecucionLog(Base):
    __tablename__ = "ejecuciones_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    mensaje: Mapped[str | None] = mapped_column(Text)
    ejecutado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
