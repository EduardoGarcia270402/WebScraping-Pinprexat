from types import SimpleNamespace

from scheduler.job_runner import _should_skip_existing_cotizacion


def test_should_not_skip_existing_quotation_when_local_pdf_is_missing(tmp_path) -> None:
    cotizacion = SimpleNamespace(ruta_pdf=str(tmp_path / "missing.pdf"))
    settings = SimpleNamespace(quotation_regenerate_existing=False)

    assert not _should_skip_existing_cotizacion(cotizacion, settings)


def test_should_skip_existing_quotation_when_local_pdf_exists(tmp_path) -> None:
    pdf_path = tmp_path / "cotizacion.pdf"
    pdf_path.write_bytes(b"%PDF-1.7")
    cotizacion = SimpleNamespace(ruta_pdf=str(pdf_path))
    settings = SimpleNamespace(quotation_regenerate_existing=False)

    assert _should_skip_existing_cotizacion(cotizacion, settings)


def test_should_not_skip_when_regeneration_is_forced(tmp_path) -> None:
    pdf_path = tmp_path / "cotizacion.pdf"
    pdf_path.write_bytes(b"%PDF-1.7")
    cotizacion = SimpleNamespace(ruta_pdf=str(pdf_path))
    settings = SimpleNamespace(quotation_regenerate_existing=True)

    assert not _should_skip_existing_cotizacion(cotizacion, settings)
