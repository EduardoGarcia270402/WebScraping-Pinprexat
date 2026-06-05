from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database.models import EjecucionLog, Funcionario, ItemCompra, LugarEntrega, Proceso


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
ITEM_FIELDS = ("numero", "cpc", "unidad", "cantidad")


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
        )
        .where(Proceso.codigo_necesidad == codigo_necesidad)
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


def _build_proceso(data: dict[str, Any]) -> Proceso:
    proceso = Proceso(**_pick(data, PROCESO_FIELDS))
    proceso.funcionario = Funcionario(**_pick(data.get("funcionario") or {}, FUNCIONARIO_FIELDS))
    proceso.lugar_entrega = LugarEntrega(**_pick(data.get("lugar_entrega") or {}, LUGAR_FIELDS))
    proceso.items_compra = [_build_item(item) for item in data.get("items_compra") or []]
    return proceso


def _build_item(data: dict[str, Any]) -> ItemCompra:
    values = _pick(data, ITEM_FIELDS)
    if values.get("cantidad") is not None:
        values["cantidad"] = Decimal(str(values["cantidad"]))
    return ItemCompra(**values)


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
            "unidad": item.unidad,
            "cantidad": item.cantidad,
        }
    )


def _normalize_item(data: dict[str, Any]) -> dict[str, Any]:
    values = _pick(data, ITEM_FIELDS)
    if values.get("cantidad") is not None:
        values["cantidad"] = Decimal(str(values["cantidad"]))
    return values


def _pick(data: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {field: data.get(field) for field in fields}
