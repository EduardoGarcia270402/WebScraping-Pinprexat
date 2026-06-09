from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


def extract_pdf_specs(pdf_path: Path) -> dict[str, Any]:
    text = extract_pdf_text(pdf_path)
    specs = extract_specs_from_text(text)
    specs["texto_extraido"] = text
    return specs


def extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to extract specification PDF text.") from exc

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return _normalize_text("\n".join(pages))


def extract_specs_from_text(text: str) -> dict[str, str | None]:
    normalized = _normalize_text(text)
    return {
        "plazo_ejecucion": _find_labeled_value(
            normalized,
            (
                "plazo de ejecucion",
                "plazo ejecucion",
                "tiempo de entrega",
                "plazo de entrega",
            ),
        ),
        "garantia": _find_labeled_value(
            normalized,
            (
                "garantia tecnica",
                "garantia",
            ),
        ),
        "validez_proforma": _find_labeled_value(
            normalized,
            (
                "validez de la proforma",
                "validez proforma",
                "vigencia de la proforma",
                "vigencia proforma",
                "validez de oferta",
            ),
        ),
        "terminos_condiciones": _find_section(
            normalized,
            (
                "terminos y condiciones",
                "condiciones generales",
                "condiciones de la contratacion",
            ),
        ),
    }


def _find_labeled_value(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        label_pattern = r"\s+".join(re.escape(part) for part in label.split())
        pattern = re.compile(
            rf"{label_pattern}\s*(?:\:|\-|\.|\n)\s*(?P<value>[^\n]{{1,220}})",
            flags=re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            value = _clean_value(match.group("value"))
            if value:
                return value

        inline_pattern = re.compile(
            rf"{label_pattern}\s+(?:es|sera|será|de)?\s*(?P<value>\d+[^\n]{{0,120}})",
            flags=re.IGNORECASE,
        )
        match = inline_pattern.search(text)
        if match:
            value = _clean_value(match.group("value"))
            if value:
                return value
    return None


def _find_section(text: str, labels: tuple[str, ...]) -> str | None:
    headings = (
        "forma de pago",
        "plazo de ejecucion",
        "garantia",
        "validez de la proforma",
        "obligaciones",
        "multas",
        "lugar de entrega",
        "presupuesto",
    )
    for label in labels:
        label_pattern = r"\s+".join(re.escape(part) for part in label.split())
        heading_pattern = "|".join(r"\s+".join(re.escape(part) for part in heading.split()) for heading in headings)
        pattern = re.compile(
            rf"{label_pattern}\s*(?:\:|\-|\n)\s*(?P<value>.*?)(?=\n\s*(?:{heading_pattern})\b|\Z)",
            flags=re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            value = _clean_value(match.group("value"))
            if value:
                return value[:2000]
    return None


def _normalize_text(value: str) -> str:
    value = _strip_accents(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip(" :-.\t")
    return cleaned or None


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
