from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from quotation.quotation_builder import QuotationData


def render_quotation_pdf(data: QuotationData, output_dir: Path) -> Path:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("Install reportlab to generate quotation PDFs.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"Cotizacion_{_safe_filename(data.numero_cotizacion)}_{_safe_filename(data.codigo_necesidad)}.pdf"

    styles = getSampleStyleSheet()
    styles["Normal"].fontSize = 10
    styles["Normal"].leading = 12
    styles["Title"].fontSize = 10
    styles["Title"].leading = 12
    styles["Title"].spaceAfter = 4
    styles["Heading2"].fontSize = 10
    styles["Heading2"].leading = 12
    styles["Heading2"].spaceBefore = 4
    styles["Heading2"].spaceAfter = 4
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=10, leading=12))
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontSize=10,
            leading=12,
            spaceBefore=8,
            spaceAfter=4,
        )
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    story = []
    logo = _logo_flowable(data)
    if logo is not None:
        story.extend([logo, Spacer(1, 8)])

    story.extend([
        Paragraph(data.company.nombre, styles["Title"]),
        Paragraph(f"Cotizacion No. {data.numero_cotizacion}", styles["Heading2"]),
        Paragraph(f"Fecha: {data.fecha:%d/%m/%Y}", styles["Normal"]),
        Spacer(1, 10),
    ])

    company_lines = [
        ("RUC", data.company.ruc),
        ("Direccion", data.company.direccion),
        ("Telefono", data.company.telefono),
        ("Email", data.company.email),
    ]
    story.extend(_details_block("Datos de la empresa", company_lines, styles))

    client_lines = [
        ("Cliente", data.client.nombre),
        ("Contacto", data.client.contacto),
        ("Correo", data.client.correo),
        ("Direccion", data.client.direccion),
        ("Provincia/Canton", _join_values(data.client.provincia, data.client.canton)),
        ("Codigo necesidad", data.codigo_necesidad),
        ("Fecha de publicacion", _format_date(data.fecha_publicacion)),
    ]
    story.extend(_details_block("Datos del cliente", client_lines, styles))

    story.append(Paragraph("Productos", styles["Section"]))
    story.append(_items_table(data, styles))

    terms_lines = [
        ("Plazo de ejecucion", data.plazo_ejecucion),
        ("Garantia", data.garantia),
        ("Validez de la proforma", data.validez_proforma),
        ("Fecha limite de entrega", _format_date(data.fecha_limite_entrega)),
    ]
    story.extend(_details_block("Terminos y condiciones", terms_lines, styles))
    if data.terminos_condiciones:
        story.append(Paragraph(_escape(data.terminos_condiciones), styles["Small"]))

    doc.build(story)
    return pdf_path


def _logo_flowable(data: QuotationData) -> object | None:
    logo_path = data.company.logo_path
    if logo_path is None or not logo_path.exists():
        return None

    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image

    reader = ImageReader(str(logo_path))
    width, height = reader.getSize()
    max_width = 8.5 * cm
    max_height = 2.3 * cm
    scale = min(max_width / width, max_height / height)
    image = Image(str(logo_path), width=width * scale, height=height * scale)
    image.hAlign = "CENTER"
    return image


def _details_block(title: str, rows: list[tuple[str, str | None]], styles: object) -> list[object]:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    table_data = [
        [Paragraph(f"<b>{_escape(label)}</b>", styles["Small"]), Paragraph(_escape(value or "N/D"), styles["Small"])]
        for label, value in rows
    ]
    table = Table(table_data, colWidths=[120, 380])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [Paragraph(title, styles["Section"]), table]


def _items_table(data: QuotationData, styles: object) -> object:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    rows = [[
        Paragraph("<b>No.</b>", styles["Small"]),
        Paragraph("<b>CPC</b>", styles["Small"]),
        Paragraph("<b>Descripcion</b>", styles["Small"]),
        Paragraph("<b>Unidad</b>", styles["Small"]),
        Paragraph("<b>Cantidad</b>", styles["Small"]),
    ]]
    for item in data.items:
        rows.append(
            [
                item.numero or "",
                _escape(item.codigo or ""),
                Paragraph(_escape(item.descripcion or "N/D"), styles["Small"]),
                _escape(item.unidad or ""),
                _format_decimal(item.cantidad),
            ]
        )

    if len(rows) == 1:
        rows.append(["", "", Paragraph("Sin productos registrados", styles["Small"]), "", ""])

    table = Table(rows, colWidths=[34, 82, 245, 70, 70], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value:,.2f}"


def _format_date(value: object | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%d/%m/%Y")


def _join_values(*values: str | None) -> str | None:
    present = [value for value in values if value]
    return " / ".join(present) if present else None


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_filename(value: str) -> str:
    import re

    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return re.sub(r"_+", "_", cleaned).strip("_") or "cotizacion"
