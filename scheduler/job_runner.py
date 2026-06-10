from __future__ import annotations

import unicodedata
from collections.abc import Callable
from hashlib import sha1
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from config.settings import get_settings
from database.connection import SessionLocal
from database.repository import (
    get_cotizacion_by_numero,
    get_latest_cotizacion,
    registrar_ejecucion,
    save_cotizacion,
    save_especificaciones_pdf,
    save_proceso,
)
from notifier.email_notifier import send_email
from notifier.telegram_notifier import send_telegram
from parser.nco_parser import parse_nco_detail
from parser.pdf_specs_parser import extract_pdf_specs
from quotation.pdf_renderer import render_quotation_pdf
from quotation.quotation_builder import build_quotation_data, generate_quotation_number
from scraper.document_downloader import download_document
from scraper.drive_uploader import upload_to_drive
from scraper.firecrawl_client import FirecrawlScraper


def read_target_urls() -> list[str]:
    settings = get_settings()
    if not settings.targets_file.exists():
        return []

    urls: list[str] = []
    seen: set[str] = set()
    for line in settings.targets_file.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if not url or url.startswith("#") or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def run_scraper_job(scraper_factory: Callable[[], FirecrawlScraper] = FirecrawlScraper) -> None:
    settings = get_settings()
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(settings.log_file, rotation="1 MB", retention="14 days", enqueue=True)

    urls = read_target_urls()
    if not urls:
        logger.warning("No target URLs configured")
        return

    scraper = scraper_factory()
    for url in urls:
        _process_url(url, scraper)


def start_scheduler() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone="America/Guayaquil")
    for hour in settings.schedule_hours:
        scheduler.add_job(run_scraper_job, "cron", hour=hour, minute=0, id=f"sercop_scraper_{hour}")

    logger.info("Scheduler started for hours: {}", settings.schedule_hours)
    scheduler.start()


def _process_url(url: str, scraper: FirecrawlScraper) -> None:
    with SessionLocal() as session:
        try:
            raw_content = scraper.scrape(url)
            _save_raw_response(url, raw_content)
            parsed = parse_nco_detail(raw_content)
            _process_documentos_anexos(url, parsed)
            result = save_proceso(session, parsed)
            session.flush()
            _process_cotizacion(session, result.proceso)

            estado_log = "sin_cambios" if result.estado == "sin_cambios" else "exitoso"
            mensaje = _build_result_message(result.estado, parsed.get("codigo_necesidad"), result.cambios)
            registrar_ejecucion(session, url, estado_log, mensaje)
            session.commit()

            logger.info("{}: {}", result.estado, url)
            if result.estado in {"nuevo", "actualizado"}:
                _notify(f"SERCOP proceso {result.estado}", mensaje)
        except Exception as exc:
            session.rollback()
            registrar_ejecucion(session, url, "error", str(exc))
            session.commit()
            logger.exception("Error processing {}", url)
            _notify("SERCOP scraper error", f"URL: {url}\nError: {exc}")


def _notify(subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.notifications_enabled:
        logger.info("Notifications disabled. Skipping notification: {}", subject)
        return

    try:
        send_email(subject, body)
    except Exception:
        logger.exception("Email notification failed")

    try:
        send_telegram(f"{subject}\n\n{body}")
    except Exception:
            logger.exception("Telegram notification failed")


def _process_documentos_anexos(url: str, parsed: dict[str, object]) -> None:
    settings = get_settings()
    documentos = parsed.get("documentos_anexos")
    codigo = parsed.get("codigo_necesidad")
    if not isinstance(documentos, list):
        parsed["documentos_anexos"] = []
        return

    documento_filtrado = _select_especificaciones_document(documentos)
    parsed["documentos_anexos"] = []

    if not settings.download_documents or documento_filtrado is None or not isinstance(codigo, str):
        return

    documentos_procesados: list[dict[str, object]] = []
    for documento in [documento_filtrado]:
        descripcion = documento.get("descripcion_archivo")
        download_url = documento.get("download_url")
        if not isinstance(descripcion, str) or not isinstance(download_url, str):
            continue

        try:
            download_result = download_document(
                page_url=url,
                download_url=download_url,
                descripcion=descripcion,
                codigo_necesidad=codigo,
                output_dir=settings.documents_dir,
            )
            documento.update(download_result)

            if settings.drive_upload_enabled:
                credentials_file = (
                    settings.drive_oauth_client_file
                    if settings.drive_auth_mode == "oauth"
                    else settings.drive_service_account_file
                )
                if credentials_file is None:
                    raise ValueError("Google Drive credentials file is required when DRIVE_UPLOAD_ENABLED=true")

                drive_result = upload_to_drive(
                    local_path=settings.documents_dir / download_result["nombre_archivo"],
                    credentials_file=credentials_file,
                    folder_name=settings.drive_folder_name,
                    folder_id=settings.drive_folder_id,
                    auth_mode=settings.drive_auth_mode,
                    token_file=settings.drive_oauth_token_file,
                )
                documento.update(drive_result)
            documentos_procesados.append(documento)
        except Exception as exc:
            logger.warning("Attached document was downloaded but not uploaded: {} ({})", descripcion, exc)

    parsed["documentos_anexos"] = documentos_procesados


def _process_cotizacion(session, proceso) -> None:
    settings = get_settings()
    if not settings.quotation_enabled:
        return

    latest_cotizacion = get_latest_cotizacion(session, proceso)
    if latest_cotizacion is not None and _should_skip_existing_cotizacion(latest_cotizacion, settings):
        return

    specs = None
    documento = _select_local_pdf_document(proceso.documentos_anexos)
    if documento is not None and documento.ruta_local:
        try:
            specs_data = extract_pdf_specs(Path(documento.ruta_local))
            specs_data["documento_anexo_id"] = documento.id
            specs = save_especificaciones_pdf(session, proceso, specs_data)
        except Exception as exc:
            logger.warning("Specification PDF extraction failed for {}: {}", proceso.codigo_necesidad, exc)

    try:
        numero_cotizacion = _build_unique_quotation_number(session)
        quotation_data = build_quotation_data(
            proceso=proceso,
            specs=specs or proceso.especificaciones_pdf,
            settings=settings,
            numero_cotizacion=numero_cotizacion,
        )
        pdf_path = render_quotation_pdf(quotation_data, settings.quotations_dir)
        cotizacion_data = {
            "numero_cotizacion": quotation_data.numero_cotizacion,
            "fecha": quotation_data.fecha,
            "ruta_pdf": str(pdf_path),
            "estado": "generada",
        }

        if settings.drive_upload_enabled:
            credentials_file = (
                settings.drive_oauth_client_file
                if settings.drive_auth_mode == "oauth"
                else settings.drive_service_account_file
            )
            if credentials_file is None:
                raise ValueError("Google Drive credentials file is required when DRIVE_UPLOAD_ENABLED=true")

            drive_result = upload_to_drive(
                local_path=pdf_path,
                credentials_file=credentials_file,
                folder_name=settings.quotation_drive_folder_name,
                folder_id=settings.quotation_drive_folder_id,
                auth_mode=settings.drive_auth_mode,
                token_file=settings.drive_oauth_token_file,
            )
            cotizacion_data.update(drive_result)

        save_cotizacion(session, proceso, cotizacion_data)
        logger.info("Quotation generated for {}: {}", proceso.codigo_necesidad, pdf_path)
    except Exception as exc:
        logger.warning("Quotation generation failed for {}: {}", proceso.codigo_necesidad, exc)


def _select_local_pdf_document(documentos: list[object]):
    for documento in documentos:
        ruta_local = getattr(documento, "ruta_local", None)
        nombre_archivo = getattr(documento, "nombre_archivo", "") or ""
        if ruta_local and nombre_archivo.lower().endswith(".pdf"):
            return documento
    return None


def _should_skip_existing_cotizacion(cotizacion, settings) -> bool:
    if settings.quotation_regenerate_existing:
        return False

    if not cotizacion.ruta_pdf:
        return False

    return Path(cotizacion.ruta_pdf).exists()


def _build_unique_quotation_number(session) -> str:
    for _ in range(20):
        numero = generate_quotation_number()
        if get_cotizacion_by_numero(session, numero) is None:
            return numero
    raise RuntimeError("Could not generate a unique quotation number")


def _select_especificaciones_document(documentos: list[object]) -> dict[str, object] | None:
    candidates = [documento for documento in documentos if isinstance(documento, dict)]
    exact_matches = [
        documento
        for documento in candidates
        if _is_exact_especificaciones_tecnicas(documento.get("descripcion_archivo"))
    ]
    if exact_matches:
        return exact_matches[0]

    fallback_matches = [
        documento
        for documento in candidates
        if _is_especificaciones_tecnicas(documento.get("descripcion_archivo"))
    ]
    return fallback_matches[0] if fallback_matches else None


def _is_exact_especificaciones_tecnicas(value: object) -> bool:
    normalized = _normalize_document_description(value)
    compact = normalized.replace(" ", "")
    return normalized in {"especificaciones tecnicas", "terminos de referencia"} or compact == "terminosdereferencia"


def _is_especificaciones_tecnicas(value: object) -> bool:
    normalized = _normalize_document_description(value)
    compact = normalized.replace(" ", "")
    return (
        "especificaciones" in normalized
        or "terminos de referencia" in normalized
        or "terminosdereferencia" in compact
        or normalized == "tdr"
    )


def _normalize_document_description(value: object) -> str:
    if not isinstance(value, str):
        return ""

    normalized = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    normalized = " ".join(normalized.lower().split())
    return normalized


def _save_raw_response(url: str, raw_content: str) -> None:
    settings = get_settings()
    if not settings.save_raw_responses:
        return

    settings.raw_responses_dir.mkdir(parents=True, exist_ok=True)
    digest = sha1(url.encode("utf-8")).hexdigest()[:12]
    raw_file = settings.raw_responses_dir / f"{digest}.md"
    raw_file.write_text(raw_content, encoding="utf-8")
    logger.info("Raw response saved: {}", raw_file)


def _build_result_message(estado: str, codigo: str | None, cambios: dict[str, object]) -> str:
    lines = [f"Estado: {estado}", f"Codigo necesidad: {codigo or 'N/D'}"]
    if cambios:
        lines.append("Cambios detectados:")
        for field, values in cambios.items():
            lines.append(f"- {field}: {values}")
    return "\n".join(lines)
