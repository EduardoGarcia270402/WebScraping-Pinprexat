from database.models import DocumentoAnexo, EspecificacionPDF, Proceso
from database.repository import _replace_documentos_if_changed


def test_replace_documentos_detaches_specs_from_removed_document() -> None:
    proceso = Proceso(codigo_necesidad="NIC-001")
    proceso.documentos_anexos = [
        DocumentoAnexo(
            id=12,
            descripcion_archivo="ESPECIFICACIONES TECNICAS",
            nombre_archivo="old.pdf",
            ruta_local="downloads/old.pdf",
        )
    ]
    proceso.especificaciones_pdf = EspecificacionPDF(documento_anexo_id=12)

    changes = _replace_documentos_if_changed(
        proceso,
        [
            {
                "descripcion_archivo": "ESPECIFICACIONES TECNICAS",
                "nombre_archivo": "new.pdf",
                "ruta_local": "downloads/new.pdf",
            }
        ],
    )

    assert changes is not None
    assert proceso.especificaciones_pdf.documento_anexo_id is None
    assert proceso.documentos_anexos[0].nombre_archivo == "new.pdf"


def test_replace_documentos_preserves_download_and_drive_metadata() -> None:
    proceso = Proceso(codigo_necesidad="NIC-002")
    proceso.documentos_anexos = [
        DocumentoAnexo(
            descripcion_archivo="TERMINOSDEREFERENCIA",
            download_url="https://example.com/tdr",
            nombre_archivo="EspecificacionesTecnicas_NIC-002.pdf",
            ruta_local="downloads/EspecificacionesTecnicas_NIC-002.pdf",
            drive_file_id="drive-id",
            drive_url="https://drive.google.com/file/d/drive-id/view",
        )
    ]

    changes = _replace_documentos_if_changed(
        proceso,
        [
            {
                "descripcion_archivo": "TERMINOSDEREFERENCIA",
                "download_url": "https://example.com/tdr",
            }
        ],
    )

    assert changes is None
    assert proceso.documentos_anexos[0].nombre_archivo == "EspecificacionesTecnicas_NIC-002.pdf"
    assert proceso.documentos_anexos[0].drive_file_id == "drive-id"
