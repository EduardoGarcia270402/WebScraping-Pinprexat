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
        "plazo_ejecucion": _find_condition_summary(
            normalized,
            (
                "plazo de ejecucion",
                "plazo ejecucion",
                "tiempo de entrega",
                "plazo de entrega",
            ),
        ),
        "garantia": _find_condition_summary(
            normalized,
            (
                "garantias tecnicas",
                "garantia tecnica",
                "garantias",
                "garantia",
                "garantia minima",
            ),
        ),
        "validez_proforma": _find_condition_summary(
            normalized,
            (
                "validez de la proforma",
                "validez proforma",
                "validez de proforma",
                "vigencia de la proforma",
                "vigencia proforma",
                "vigencia de oferta",
                "vigencia de la oferta",
                "validez de oferta",
                "validez oferta",
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


def _find_condition_summary(text: str, labels: tuple[str, ...]) -> str | None:
    keyword_summary = _find_keyword_condition_summary(text, labels)
    if keyword_summary:
        return keyword_summary

    section = _find_labeled_section(text, labels)
    if section:
        summary = _summarize_condition(section)
        if summary:
            return summary

    value = _find_labeled_value(text, labels)
    if value:
        return _summarize_condition(value) or value

    return None


def _find_labeled_section(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        label_pattern = r"\s+".join(re.escape(part) for part in label.split())
        pattern = re.compile(
            rf"(?:^|\n)\s*(?:\d+\s*[\.\)]\s*)?{label_pattern}\s*(?P<value>.*?)(?=\n\s*(?:\d+\s*[\.\)]\s*)?[A-Z][A-Z0-9 /,.-]{{2,}}\s*(?:\n|$)|\Z)",
            flags=re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            value = _clean_value(match.group("value"))
            if value and not _looks_like_heading(value):
                return value
    return None


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
            if value and not _looks_like_heading(value):
                return _find_duration_sentence(value) or value

        inline_pattern = re.compile(
            rf"{label_pattern}\s+(?:es|sera|de|minima|minimo)?\s*(?P<value>\d+[^\n]{{0,120}})",
            flags=re.IGNORECASE,
        )
        match = inline_pattern.search(text)
        if match:
            value = _clean_value(match.group("value"))
            if value and not _looks_like_heading(value):
                return value

        context_pattern = re.compile(
            rf"{label_pattern}(?P<context>.{{0,320}})",
            flags=re.IGNORECASE | re.DOTALL,
        )
        match = context_pattern.search(text)
        if match:
            value = _find_duration_sentence(match.group("context"))
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


def _find_keyword_condition_summary(text: str, labels: tuple[str, ...]) -> str | None:
    keywords = _condition_keywords(labels)
    if not keywords:
        return None

    for keyword in keywords:
        pattern = re.compile(
            rf"{keyword}\w*\s+(?P<context>.{{0,260}})",
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(text):
            summary = _summarize_condition(
                match.group("context"),
                max_words=9 if keyword == "garantia" else 10,
                require_duration=True,
            )
            if summary:
                return summary
    return None


def _condition_keywords(labels: tuple[str, ...]) -> tuple[str, ...]:
    joined = " ".join(labels)
    if "garantia" in joined:
        return ("garantia",)
    if "vigencia" in joined or "validez" in joined:
        return ("vigente", "vigencia", "validez")
    if "plazo" in joined:
        return ("plazo",)
    return ()


def _summarize_condition(value: str, max_words: int = 10, require_duration: bool = False) -> str | None:
    duration = _find_duration_sentence(value)
    if require_duration and duration is None:
        return None

    candidate = duration or _clean_value(value)
    if not candidate or _looks_like_heading(candidate):
        return None

    words = candidate.split()
    return " ".join(words[:max_words]).strip(" ,;:-.")


def _looks_like_heading(value: str) -> bool:
    normalized = value.strip(" :-.\t")
    if not normalized:
        return False
    if re.fullmatch(r"\d+\s*[\.\)]?\s*[A-Za-z ]+", normalized):
        return True
    words = normalized.split()
    return len(words) <= 4 and normalized.upper() == normalized and any(char.isalpha() for char in normalized)


def _find_duration_sentence(value: str) -> str | None:
    lines = [line.strip(" -:\t") for line in value.splitlines() if line.strip(" -:\t")]
    candidates = lines or [value]
    duration_pattern = re.compile(
        r"(?:minim[ao]\s+)?(?:de\s+)?(?:\d+|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|quince|treinta|cuarenta|sesenta|noventa)(?:\s*\(\d+\))?\s*(?:dia|dias|mes|meses|ano|anos)\b[^.;\n]*",
        flags=re.IGNORECASE,
    )
    for candidate in candidates:
        match = duration_pattern.search(candidate)
        if match:
            return _clean_value(match.group(0))
    return None


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
