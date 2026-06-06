from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


def _getenv(name: str, default: str | None = None) -> str | None:
    from os import getenv

    value = getenv(name)
    if value is None or value == "":
        return default
    return value


def _getenv_int(name: str, default: int) -> int:
    value = _getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _getenv_bool(name: str, default: bool) -> bool:
    value = _getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _getenv_hours(name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    value = _getenv(name)
    if value is None:
        return default

    hours: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            hour = int(item)
        except ValueError as exc:
            raise ValueError(f"{name} must contain comma-separated integers") from exc
        if hour < 0 or hour > 23:
            raise ValueError(f"{name} hours must be between 0 and 23")
        hours.append(hour)

    return tuple(hours) or default


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    firecrawl_api_key: str | None
    email_smtp_host: str
    email_smtp_port: int
    email_user: str | None
    email_password: str | None
    email_destinatario: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    notifications_enabled: bool
    save_raw_responses: bool
    download_documents: bool
    documents_dir: Path
    drive_upload_enabled: bool
    drive_auth_mode: str
    drive_service_account_file: Path | None
    drive_oauth_client_file: Path | None
    drive_oauth_token_file: Path
    drive_folder_id: str | None
    drive_folder_name: str
    schedule_hours: tuple[int, ...]
    targets_file: Path
    log_file: Path
    raw_responses_dir: Path

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")

    return Settings(
        db_host=_getenv("DB_HOST", "localhost") or "localhost",
        db_port=_getenv_int("DB_PORT", 5432),
        db_name=_getenv("DB_NAME", "sercop_db") or "sercop_db",
        db_user=_getenv("DB_USER", "postgres") or "postgres",
        db_password=_getenv("DB_PASSWORD", "") or "",
        firecrawl_api_key=_getenv("FIRECRAWL_API_KEY"),
        email_smtp_host=_getenv("EMAIL_SMTP_HOST", "smtp.gmail.com") or "smtp.gmail.com",
        email_smtp_port=_getenv_int("EMAIL_SMTP_PORT", 587),
        email_user=_getenv("EMAIL_USER"),
        email_password=_getenv("EMAIL_PASSWORD"),
        email_destinatario=_getenv("EMAIL_DESTINATARIO"),
        telegram_bot_token=_getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_getenv("TELEGRAM_CHAT_ID"),
        notifications_enabled=_getenv_bool("NOTIFICATIONS_ENABLED", False),
        save_raw_responses=_getenv_bool("SAVE_RAW_RESPONSES", False),
        download_documents=_getenv_bool("DOWNLOAD_DOCUMENTS", True),
        documents_dir=BASE_DIR / (_getenv("DOCUMENTS_DIR", "downloads/documentos_anexos") or "downloads/documentos_anexos"),
        drive_upload_enabled=_getenv_bool("DRIVE_UPLOAD_ENABLED", False),
        drive_auth_mode=_getenv("DRIVE_AUTH_MODE", "service_account") or "service_account",
        drive_service_account_file=(
            BASE_DIR / service_account_file
            if (service_account_file := _getenv("DRIVE_SERVICE_ACCOUNT_FILE"))
            else None
        ),
        drive_oauth_client_file=(
            BASE_DIR / oauth_client_file
            if (oauth_client_file := _getenv("DRIVE_OAUTH_CLIENT_FILE"))
            else None
        ),
        drive_oauth_token_file=BASE_DIR
        / (_getenv("DRIVE_OAUTH_TOKEN_FILE", "credentials/google-drive-token.json") or "credentials/google-drive-token.json"),
        drive_folder_id=_getenv("DRIVE_FOLDER_ID"),
        drive_folder_name=_getenv("DRIVE_FOLDER_NAME", "NecesidadesContratacion") or "NecesidadesContratacion",
        schedule_hours=_getenv_hours("SCHEDULE_HOURS", (8, 14, 20)),
        targets_file=BASE_DIR / "urls" / "targets.txt",
        log_file=BASE_DIR / "logs" / "scraper.log",
        raw_responses_dir=BASE_DIR / "logs" / "raw",
    )
