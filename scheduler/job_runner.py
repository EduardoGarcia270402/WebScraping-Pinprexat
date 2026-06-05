from __future__ import annotations

from collections.abc import Callable
from hashlib import sha1

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from config.settings import get_settings
from database.connection import SessionLocal
from database.repository import registrar_ejecucion, save_proceso
from notifier.email_notifier import send_email
from notifier.telegram_notifier import send_telegram
from parser.nco_parser import parse_nco_detail
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
            result = save_proceso(session, parsed)

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
