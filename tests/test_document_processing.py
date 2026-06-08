from scheduler.job_runner import _is_especificaciones_tecnicas, _select_especificaciones_document
from scraper.document_downloader import _build_filename, _is_pdf_content


def test_especificaciones_filter_matches_real_sercop_variants() -> None:
    assert _is_especificaciones_tecnicas("ESPECIFICACIONES TECNICAS")
    assert _is_especificaciones_tecnicas("Especificaciones tecnicas")
    assert _is_especificaciones_tecnicas("SOLICITUD DE PUBLICACION ESPECIFICACIONES")
    assert not _is_especificaciones_tecnicas("ANALISIS VINCULACION Y PROYECTO ORDEN DE COMPRA")


def test_select_especificaciones_document_prefers_exact_match() -> None:
    documentos = [
        {"descripcion_archivo": "SOLICITUD DE PUBLICACION ESPECIFICACIONES", "download_url": "wrong"},
        {"descripcion_archivo": "ESPECIFICACIONES TECNICAS", "download_url": "right"},
    ]

    assert _select_especificaciones_document(documentos) == documentos[1]


def test_especificaciones_tecnicas_filename_uses_contract_code() -> None:
    filename = _build_filename(
        descripcion="SOLICITUD DE PUBLICACION ESPECIFICACIONES",
        codigo_necesidad="NIC-1865033840001-2026-00037",
        download_url="https://example.com/download",
        content_disposition=None,
    )

    assert filename == "EspecificacionesTecnicas_NIC-1865033840001-2026-00037.pdf"


def test_pdf_content_detection() -> None:
    assert _is_pdf_content(b"%PDF-1.7\ncontent")
    assert _is_pdf_content(b"  \n%PDF-1.4\ncontent")
    assert not _is_pdf_content(b"PK\x03\x04zip-content")
