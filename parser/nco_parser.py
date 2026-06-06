from __future__ import annotations

import re
import unicodedata
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
    data["items_compra"] = _parse_items(raw_content, text)
    data["documentos_anexos"] = _parse_documentos_anexos(raw_content)
    data["proveedores"] = _parse_proveedores(raw_content)
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


def _parse_items(raw_content: str, text: str) -> list[dict[str, Any]]:
    html_items = _parse_html_items(raw_content)
    if html_items:
        return html_items

    items: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        cells = [_clean_value(cell) for cell in line.strip("|").split("|")]
        cells = [cell for cell in cells if cell and not set(cell) <= {"-", ":"}]
        normalized_cells = [_strip_accents(cell).lower() for cell in cells]
        if {"no.", "cpc", "unidad", "cantidad"}.issubset(set(normalized_cells)):
            continue
        item = _item_from_cells(cells)
        if item:
            items.append(item)

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


def _parse_html_items(raw_content: str) -> list[dict[str, Any]]:
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", raw_content, flags=re.IGNORECASE | re.DOTALL)
    items: list[dict[str, Any]] = []

    for row in rows:
        cells = _extract_html_cells(row)
        item = _item_from_cells(cells)
        if item:
            items.append(item)

    return items


def _parse_documentos_anexos(raw_content: str) -> list[dict[str, Any]]:
    table = _find_section_table(raw_content, "Documentos Anexos")
    if not table:
        return []

    documentos: list[dict[str, Any]] = []
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, flags=re.IGNORECASE | re.DOTALL)
    for row in rows:
        href_match = re.search(r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"']", row, flags=re.IGNORECASE | re.DOTALL)
        if not href_match:
            continue

        cells = _extract_html_cells(row)
        if not cells:
            continue

        documentos.append(
            {
                "descripcion_archivo": cells[0],
                "download_url": unescape(href_match.group("href")),
            }
        )

    return documentos


def _parse_proveedores(raw_content: str) -> list[dict[str, Any]]:
    table = _find_section_table(raw_content, "Proveedores")
    if not table:
        return []

    proveedores: list[dict[str, Any]] = []
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, flags=re.IGNORECASE | re.DOTALL)
    for row in rows:
        cells = _extract_html_cells(row)
        if len(cells) < 3:
            continue

        numero = _parse_int(cells[0])
        if numero is None:
            continue

        proveedores.append(
            {
                "numero": numero,
                "ruc_id": cells[1],
                "razon_social": cells[2],
            }
        )

    return proveedores


def _find_section_table(raw_content: str, section_title: str) -> str | None:
    headers = re.finditer(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", raw_content, flags=re.IGNORECASE | re.DOTALL)
    normalized_title = _normalize_match_text(section_title)
    for header in headers:
        header_text = _normalize_match_text(header.group(1))
        if normalized_title not in header_text:
            continue

        table_match = re.search(r"<table\b[^>]*>.*?</table>", raw_content[header.end() :], flags=re.IGNORECASE | re.DOTALL)
        if table_match:
            return table_match.group(0)
    return None


def _extract_html_cells(row: str) -> list[str]:
    raw_cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, flags=re.IGNORECASE | re.DOTALL)
    cells: list[str] = []
    for cell in raw_cells:
        cell = re.sub(r"<br\s*/?>", "\n", cell, flags=re.IGNORECASE)
        cell = re.sub(r"<[^>]+>", " ", cell)
        value = _clean_value(unescape(cell))
        if value:
            cells.append(value)
    return cells


def _item_from_cells(cells: list[str]) -> dict[str, Any] | None:
    if len(cells) < 4:
        return None

    numero = _parse_int(cells[0])
    cantidad = _parse_decimal(cells[-1])
    if numero is None or cantidad is None:
        return None

    item = {
        "numero": numero,
        "cpc": cells[1],
        "unidad": cells[-2],
        "cantidad": cantidad,
    }
    if len(cells) >= 6:
        item["categoria_cpc"] = cells[2]
        item["descripcion_producto"] = cells[3]
    return item


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
    translated = value.translate(replacements)
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", translated)
        if not unicodedata.combining(char)
    )


def _normalize_match_text(value: str) -> str:
    text = unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _strip_accents(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()
