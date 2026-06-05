from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html import unescape
from typing import Any


LABELS = {
    "nombre_entidad": ("Nombre Entidad", "Entidad"),
    "tipo_necesidad": ("Tipo de Necesidad",),
    "codigo_necesidad": ("Codigo Necesidad de Contratacion", "Codigo Necesidad", "Codigo"),
    "estado_necesidad": ("Estado de la Necesidad", "Estado Necesidad", "Estado"),
    "fecha_publicacion": ("Fecha de Publicacion",),
    "fecha_limite": ("Fecha Limite", "Fecha limite"),
}

FUNCIONARIO_LABELS = {
    "nombre": ("Nombre", "Funcionario Encargado"),
    "correo": ("Correo Electronico", "Correo", "Email", "E-mail"),
}

LUGAR_LABELS = {
    "provincia": ("Provincia",),
    "canton": ("Canton",),
    "parroquia": ("Parroquia",),
    "direccion": ("Direccion",),
}


def parse_nco_detail(raw_content: str) -> dict[str, Any]:
    text = _normalize_text(raw_content)

    data: dict[str, Any] = {}
    for field, labels in LABELS.items():
        data[field] = _find_value(text, labels)

    data["fecha_publicacion"] = _parse_date(data["fecha_publicacion"])
    data["fecha_limite"] = _parse_date(data["fecha_limite"])
    data["funcionario"] = {
        field: _find_value(text, labels)
        for field, labels in FUNCIONARIO_LABELS.items()
    }
    data["lugar_entrega"] = {
        field: _find_value(text, labels)
        for field, labels in LUGAR_LABELS.items()
    }
    data["items_compra"] = _parse_items(text)
    return data


def _normalize_text(raw_content: str) -> str:
    text = unescape(raw_content)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _strip_accents(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _find_value(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        escaped = re.escape(_strip_accents(label))
        patterns = (
            rf"{escaped}\s*[:\-]\s*(?P<value>[^\n|]+)",
            rf"\|\s*{escaped}\s*\|\s*(?P<value>[^|]+)\|",
        )
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = _clean_value(match.group("value"))
                if value:
                    return value
    return None


def _parse_items(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        cells = [_clean_value(cell) for cell in line.strip("|").split("|")]
        cells = [cell for cell in cells if cell and not set(cell) <= {"-", ":"}]
        normalized_cells = [_strip_accents(cell).lower() for cell in cells]
        if {"no.", "cpc", "unidad", "cantidad"}.issubset(set(normalized_cells)):
            continue
        if len(cells) >= 4 and _looks_like_item(cells):
            items.append(
                {
                    "numero": _parse_int(cells[0]),
                    "cpc": cells[1],
                    "unidad": cells[2],
                    "cantidad": _parse_decimal(cells[3]),
                }
            )

    if items:
        return items

    pattern = re.compile(
        r"(?P<numero>\d+)\s+(?P<cpc>\d{5,}[\d.]*)\s+(?P<unidad>[A-Za-z ]+?)\s+(?P<cantidad>\d+(?:[.,]\d+)?)",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        items.append(
            {
                "numero": _parse_int(match.group("numero")),
                "cpc": _clean_value(match.group("cpc")),
                "unidad": _clean_value(match.group("unidad")),
                "cantidad": _parse_decimal(match.group("cantidad")),
            }
        )

    return items


def _looks_like_item(cells: list[str]) -> bool:
    return _parse_int(cells[0]) is not None and _parse_decimal(cells[3]) is not None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    value = value.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue
    return None


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    return int(match.group()) if match else None


def _parse_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    normalized = value.strip()
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[*_`]+", "", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" :-|\t")
    return cleaned or None


def _strip_accents(value: str) -> str:
    replacements = str.maketrans(
        "áéíóúÁÉÍÓÚñÑüÜ",
        "aeiouAEIOUnNuU",
    )
    return value.translate(replacements)
