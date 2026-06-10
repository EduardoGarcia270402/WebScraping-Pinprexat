from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings
from database.models import Base


def create_db_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_document_specs_constraint()


def _ensure_document_specs_constraint() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE especificaciones_pdf "
                "DROP CONSTRAINT IF EXISTS especificaciones_pdf_documento_anexo_id_fkey"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE especificaciones_pdf "
                "ADD CONSTRAINT especificaciones_pdf_documento_anexo_id_fkey "
                "FOREIGN KEY (documento_anexo_id) "
                "REFERENCES documentos_anexos(id) "
                "ON DELETE SET NULL"
            )
        )


def check_db_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
