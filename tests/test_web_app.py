from pathlib import Path
from types import SimpleNamespace

from web.app import _prepare_documentos, create_app


def test_index_shows_url_entry_form() -> None:
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Carga una necesidad de SERCOP" in response.data
    assert b'name="url"' in response.data


def test_load_rejects_invalid_url() -> None:
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().post("/cargar", data={"url": "no-es-url"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_quotation_hud_shows_available_documents(monkeypatch) -> None:
    from web import app as web_app

    proceso = SimpleNamespace(
        id=4,
        codigo_necesidad="NIC-004",
        nombre_entidad="Entidad",
        funcionario=None,
        lugar_entrega=None,
        items_compra=[],
        especificaciones_pdf=None,
        documentos_anexos=[
            SimpleNamespace(
                id=20,
                descripcion_archivo="TERMINOSDEREFERENCIA",
                nombre_archivo=None,
                ruta_local=None,
                drive_url=None,
            )
        ],
    )

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(web_app, "SessionLocal", FakeSession)
    monkeypatch.setattr(web_app, "get_proceso_by_id", lambda session, proceso_id: proceso)

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/cotizaciones/nueva/4")

    assert response.status_code == 200
    assert b"Documentos disponibles" in response.data
    assert b"TERMINOSDEREFERENCIA" in response.data
    assert b"/documentos/20/descargar?proceso_id=4" in response.data


def test_prepare_documentos_keeps_all_documents_and_resolves_urls() -> None:
    documentos = [
        {"descripcion_archivo": "TDR", "download_url": "../descargar/tdr"},
        {"descripcion_archivo": "Informe", "download_url": "/archivos/informe.pdf"},
    ]

    result = _prepare_documentos(
        "https://compraspublicas.gob.ec/Proceso/NCO/detalle",
        documentos,
    )

    assert len(result) == 2
    assert result[0]["download_url"] == "https://compraspublicas.gob.ec/Proceso/descargar/tdr"
    assert result[1]["download_url"] == "https://compraspublicas.gob.ec/archivos/informe.pdf"


def test_download_attachment_uses_normalized_filename_and_uploads_to_drive(
    monkeypatch,
    tmp_path,
) -> None:
    from web import app as web_app

    proceso = SimpleNamespace(id=8, codigo_necesidad="NIC-008")
    documento = SimpleNamespace(
        id=12,
        proceso=proceso,
        descripcion_archivo="TERMINOSDEREFERENCIA",
        download_url="https://example.com/tdr",
        nombre_archivo=None,
        ruta_local=None,
        drive_file_id=None,
        drive_url=None,
    )
    uploaded_paths = []

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self):
            return None

    def fake_download(**kwargs):
        filename = "EspecificacionesTecnicas_NIC-008.pdf"
        path = tmp_path / filename
        path.write_bytes(b"%PDF-1.7 test")
        return {
            "download_url": kwargs["download_url"],
            "nombre_archivo": filename,
            "ruta_local": str(path),
        }

    def fake_upload(local_path, settings):
        uploaded_paths.append(local_path)
        return {
            "drive_file_id": "drive-id",
            "drive_url": "https://drive.google.com/file/d/drive-id/view",
        }

    monkeypatch.setattr(web_app, "SessionLocal", FakeSession)
    monkeypatch.setattr(web_app, "get_documento_by_id", lambda session, documento_id: documento)
    monkeypatch.setattr(web_app, "download_document", fake_download)
    monkeypatch.setattr(web_app, "_upload_attachment", fake_upload)
    monkeypatch.setattr(web_app, "_update_specs_from_document", lambda *args: None)
    monkeypatch.setattr(
        web_app,
        "get_settings",
        lambda: SimpleNamespace(
            documents_dir=tmp_path,
            drive_upload_enabled=True,
        ),
    )

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/documentos/12/descargar?proceso_id=8")

    assert response.status_code == 200
    assert response.headers["Content-Disposition"].endswith(
        'filename=EspecificacionesTecnicas_NIC-008.pdf'
    )
    assert uploaded_paths == [Path(documento.ruta_local)]
    assert documento.drive_file_id == "drive-id"
