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
