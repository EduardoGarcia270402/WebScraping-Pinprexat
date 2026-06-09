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
    proveedores: Mapped[list[Proveedor]] = relationship(
        back_populates="proceso",
        cascade="all, delete-orphan",
    )
    documentos_anexos: Mapped[list[DocumentoAnexo]] = relationship(
        back_populates="proceso",
        cascade="all, delete-orphan",
    )
    especificaciones_pdf: Mapped[EspecificacionPDF | None] = relationship(
        back_populates="proceso",
        cascade="all, delete-orphan",
        uselist=False,
    )
    cotizaciones: Mapped[list[Cotizacion]] = relationship(
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
    categoria_cpc: Mapped[str | None] = mapped_column(String)
    descripcion_producto: Mapped[str | None] = mapped_column(Text)
    unidad: Mapped[str | None] = mapped_column(String)
    cantidad: Mapped[Decimal | None] = mapped_column(Numeric)

    proceso: Mapped[Proceso] = relationship(back_populates="items_compra")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False)
    numero: Mapped[int | None] = mapped_column(Integer)
    ruc_id: Mapped[str | None] = mapped_column(String)
    razon_social: Mapped[str | None] = mapped_column(Text)

    proceso: Mapped[Proceso] = relationship(back_populates="proveedores")


class DocumentoAnexo(Base):
    __tablename__ = "documentos_anexos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False)
    descripcion_archivo: Mapped[str | None] = mapped_column(Text)
    download_url: Mapped[str | None] = mapped_column(Text)
    nombre_archivo: Mapped[str | None] = mapped_column(String)
    ruta_local: Mapped[str | None] = mapped_column(Text)
    drive_file_id: Mapped[str | None] = mapped_column(String)
    drive_url: Mapped[str | None] = mapped_column(Text)

    proceso: Mapped[Proceso] = relationship(back_populates="documentos_anexos")


class EspecificacionPDF(Base):
    __tablename__ = "especificaciones_pdf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False, unique=True)
    documento_anexo_id: Mapped[int | None] = mapped_column(ForeignKey("documentos_anexos.id"))
    plazo_ejecucion: Mapped[str | None] = mapped_column(Text)
    garantia: Mapped[str | None] = mapped_column(Text)
    validez_proforma: Mapped[str | None] = mapped_column(Text)
    terminos_condiciones: Mapped[str | None] = mapped_column(Text)
    texto_extraido: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    proceso: Mapped[Proceso] = relationship(back_populates="especificaciones_pdf")
    documento_anexo: Mapped[DocumentoAnexo | None] = relationship()


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), nullable=False)
    numero_cotizacion: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    ruta_pdf: Mapped[str | None] = mapped_column(Text)
    drive_file_id: Mapped[str | None] = mapped_column(String)
    drive_url: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String, nullable=False, default="generada")
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    proceso: Mapped[Proceso] = relationship(back_populates="cotizaciones")


class EjecucionLog(Base):
    __tablename__ = "ejecuciones_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    mensaje: Mapped[str | None] = mapped_column(Text)
    ejecutado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
