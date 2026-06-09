from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database.models import (
    Cotizacion,
    DocumentoAnexo,
    EjecucionLog,
    EspecificacionPDF,
    Funcionario,
    ItemCompra,
    LugarEntrega,
    Proceso,
    Proveedor,
)


PROCESO_FIELDS = (
    "codigo_necesidad",
    "nombre_entidad",
    "tipo_necesidad",
    "estado_necesidad",
    "fecha_publicacion",
    "fecha_limite",
)
FUNCIONARIO_FIELDS = ("nombre", "correo")
LUGAR_FIELDS = ("provincia", "canton", "parroquia", "direccion")
ITEM_FIELDS = ("numero", "cpc", "categoria_cpc", "descripcion_producto", "unidad", "cantidad")
PROVEEDOR_FIELDS = ("numero", "ruc_id", "razon_social")
DOCUMENTO_FIELDS = (
    "descripcion_archivo",
    "download_url",
    "nombre_archivo",
    "ruta_local",
    "drive_file_id",
    "drive_url",
)
ESPECIFICACION_FIELDS = (
    "documento_anexo_id",
    "plazo_ejecucion",
    "garantia",
    "validez_proforma",
    "terminos_condiciones",
    "texto_extraido",
)
COTIZACION_FIELDS = (
    "numero_cotizacion",
    "fecha",
    "ruta_pdf",
    "drive_file_id",
    "drive_url",
    "estado",
)


@dataclass(frozen=True)
class SaveResult:
    estado: str
    proceso: Proceso
    cambios: dict[str, tuple[Any, Any]]


def get_proceso_by_codigo(session: Session, codigo_necesidad: str) -> Proceso | None:
    statement = (
        select(Proceso)
        .options(
            selectinload(Proceso.funcionario),
            selectinload(Proceso.lugar_entrega),
            selectinload(Proceso.items_compra),
            selectinload(Proceso.proveedores),
            selectinload(Proceso.documentos_anexos),
            selectinload(Proceso.especificaciones_pdf),
            selectinload(Proceso.cotizaciones),
        )
        .where(Proceso.codigo_necesidad == codigo_necesidad)
    )
    return session.scalars(statement).first()


def get_cotizacion_by_numero(session: Session, numero_cotizacion: str) -> Cotizacion | None:
    statement = select(Cotizacion).where(Cotizacion.numero_cotizacion == numero_cotizacion)
    return session.scalars(statement).first()


def get_latest_cotizacion(session: Session, proceso: Proceso) -> Cotizacion | None:
    statement = (
        select(Cotizacion)
        .where(Cotizacion.proceso_id == proceso.id)
        .order_by(Cotizacion.creado_en.desc(), Cotizacion.id.desc())
    )
    return session.scalars(statement).first()


def save_proceso(session: Session, data: dict[str, Any]) -> SaveResult:
    codigo = data.get("codigo_necesidad")
    if not codigo:
        raise ValueError("codigo_necesidad is required")

    proceso = get_proceso_by_codigo(session, codigo)
    if proceso is None:
        proceso = _build_proceso(data)
        session.add(proceso)
        return SaveResult(estado="nuevo", proceso=proceso, cambios={})

    cambios = _apply_proceso_changes(proceso, data)
    return SaveResult(
        estado="actualizado" if cambios else "sin_cambios",
        proceso=proceso,
        cambios=cambios,
    )


def registrar_ejecucion(session: Session, url: str, estado: str, mensaje: str | None = None) -> EjecucionLog:
    log = EjecucionLog(url=url, estado=estado, mensaje=mensaje)
    session.add(log)
    return log


def save_especificaciones_pdf(
    session: Session,
    proceso: Proceso,
    data: dict[str, Any],
) -> EspecificacionPDF:
    values = _pick(data, ESPECIFICACION_FIELDS)
    if proceso.especificaciones_pdf is None:
        especificaciones = EspecificacionPDF(**values)
        proceso.especificaciones_pdf = especificaciones
        session.add(especificaciones)
        return especificaciones

    for field, value in values.items():
        setattr(proceso.especificaciones_pdf, field, value)
    return proceso.especificaciones_pdf


def save_cotizacion(
    session: Session,
    proceso: Proceso,
    data: dict[str, Any],
) -> Cotizacion:
    cotizacion = Cotizacion(**_pick(data, COTIZACION_FIELDS))
    proceso.cotizaciones.append(cotizacion)
    session.add(cotizacion)
    return cotizacion


def _build_proceso(data: dict[str, Any]) -> Proceso:
    proceso = Proceso(**_pick(data, PROCESO_FIELDS))
    proceso.funcionario = Funcionario(**_pick(data.get("funcionario") or {}, FUNCIONARIO_FIELDS))
    proceso.lugar_entrega = LugarEntrega(**_pick(data.get("lugar_entrega") or {}, LUGAR_FIELDS))
    proceso.items_compra = [_build_item(item) for item in data.get("items_compra") or []]
    proceso.proveedores = [_build_proveedor(proveedor) for proveedor in data.get("proveedores") or []]
    proceso.documentos_anexos = [_build_documento(documento) for documento in data.get("documentos_anexos") or []]
    return proceso


def _build_item(data: dict[str, Any]) -> ItemCompra:
    values = _pick(data, ITEM_FIELDS)
    if values.get("cantidad") is not None:
        values["cantidad"] = Decimal(str(values["cantidad"]))
    return ItemCompra(**values)


def _build_proveedor(data: dict[str, Any]) -> Proveedor:
    return Proveedor(**_pick(data, PROVEEDOR_FIELDS))


def _build_documento(data: dict[str, Any]) -> DocumentoAnexo:
    return DocumentoAnexo(**_pick(data, DOCUMENTO_FIELDS))


def _apply_proceso_changes(proceso: Proceso, data: dict[str, Any]) -> dict[str, tuple[Any, Any]]:
    cambios: dict[str, tuple[Any, Any]] = {}
    cambios.update(_apply_fields(proceso, data, PROCESO_FIELDS, "proceso"))

    funcionario_data = data.get("funcionario") or {}
    if proceso.funcionario is None:
        proceso.funcionario = Funcionario(**_pick(funcionario_data, FUNCIONARIO_FIELDS))
        cambios["funcionario"] = (None, funcionario_data)
    else:
        cambios.update(_apply_fields(proceso.funcionario, funcionario_data, FUNCIONARIO_FIELDS, "funcionario"))

    lugar_data = data.get("lugar_entrega") or {}
    if proceso.lugar_entrega is None:
        proceso.lugar_entrega = LugarEntrega(**_pick(lugar_data, LUGAR_FIELDS))
        cambios["lugar_entrega"] = (None, lugar_data)
    else:
        cambios.update(_apply_fields(proceso.lugar_entrega, lugar_data, LUGAR_FIELDS, "lugar_entrega"))

    item_changes = _replace_items_if_changed(proceso, data.get("items_compra") or [])
    if item_changes is not None:
        cambios["items_compra"] = item_changes

    proveedor_changes = _replace_proveedores_if_changed(proceso, data.get("proveedores") or [])
    if proveedor_changes is not None:
        cambios["proveedores"] = proveedor_changes

    documento_changes = _replace_documentos_if_changed(proceso, data.get("documentos_anexos") or [])
    if documento_changes is not None:
        cambios["documentos_anexos"] = documento_changes

    return cambios


def _apply_fields(
    model: object,
    data: dict[str, Any],
    fields: Iterable[str],
    prefix: str,
) -> dict[str, tuple[Any, Any]]:
    cambios: dict[str, tuple[Any, Any]] = {}
    for field in fields:
        if field not in data:
            continue
        old_value = getattr(model, field)
        new_value = data[field]
        if old_value != new_value:
            setattr(model, field, new_value)
            cambios[f"{prefix}.{field}"] = (old_value, new_value)
    return cambios


def _replace_items_if_changed(
    proceso: Proceso,
    new_items_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    current_items = [_item_to_dict(item) for item in sorted(proceso.items_compra, key=lambda item: item.numero or 0)]
    new_items = [_normalize_item(item) for item in sorted(new_items_data, key=lambda item: item.get("numero") or 0)]

    if current_items == new_items:
        return None

    proceso.items_compra = [_build_item(item) for item in new_items]
    return current_items, new_items


def _item_to_dict(item: ItemCompra) -> dict[str, Any]:
    return _normalize_item(
        {
            "numero": item.numero,
            "cpc": item.cpc,
            "categoria_cpc": item.categoria_cpc,
            "descripcion_producto": item.descripcion_producto,
            "unidad": item.unidad,
            "cantidad": item.cantidad,
        }
    )


def _replace_proveedores_if_changed(
    proceso: Proceso,
    new_proveedores_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    current_proveedores = [
        _proveedor_to_dict(proveedor)
        for proveedor in sorted(proceso.proveedores, key=lambda proveedor: proveedor.numero or 0)
    ]
    new_proveedores = [
        _normalize_proveedor(proveedor)
        for proveedor in sorted(new_proveedores_data, key=lambda proveedor: proveedor.get("numero") or 0)
    ]

    if current_proveedores == new_proveedores:
        return None

    proceso.proveedores = [_build_proveedor(proveedor) for proveedor in new_proveedores]
    return current_proveedores, new_proveedores


def _replace_documentos_if_changed(
    proceso: Proceso,
    new_documentos_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    current_documentos = [
        _documento_to_dict(documento)
        for documento in sorted(proceso.documentos_anexos, key=lambda documento: documento.descripcion_archivo or "")
    ]
    new_documentos = [
        _normalize_documento(documento)
        for documento in sorted(new_documentos_data, key=lambda documento: documento.get("descripcion_archivo") or "")
    ]

    if current_documentos == new_documentos:
        return None

    proceso.documentos_anexos = [_build_documento(documento) for documento in new_documentos]
    return current_documentos, new_documentos


def _proveedor_to_dict(proveedor: Proveedor) -> dict[str, Any]:
    return _normalize_proveedor(
        {
            "numero": proveedor.numero,
            "ruc_id": proveedor.ruc_id,
            "razon_social": proveedor.razon_social,
        }
    )


def _documento_to_dict(documento: DocumentoAnexo) -> dict[str, Any]:
    return _normalize_documento(
        {
            "descripcion_archivo": documento.descripcion_archivo,
            "download_url": documento.download_url,
            "nombre_archivo": documento.nombre_archivo,
            "ruta_local": documento.ruta_local,
            "drive_file_id": documento.drive_file_id,
            "drive_url": documento.drive_url,
        }
    )


def _normalize_item(data: dict[str, Any]) -> dict[str, Any]:
    values = _pick(data, ITEM_FIELDS)
    if values.get("cantidad") is not None:
        values["cantidad"] = Decimal(str(values["cantidad"]))
    return values


def _normalize_proveedor(data: dict[str, Any]) -> dict[str, Any]:
    return _pick(data, PROVEEDOR_FIELDS)


def _normalize_documento(data: dict[str, Any]) -> dict[str, Any]:
    return _pick(data, DOCUMENTO_FIELDS)


def _pick(data: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {field: data.get(field) for field in fields}
