from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from database.models import EspecificacionPDF, Funcionario, ItemCompra, LugarEntrega, Proceso
from quotation.pdf_renderer import render_quotation_pdf
from quotation.quotation_builder import build_quotation_data, generate_quotation_number


def test_generate_quotation_number_uses_year_month_and_two_digits() -> None:
    number = generate_quotation_number(date(2026, 6, 8))

    assert len(number) == 8
    assert number.startswith("202606")
    assert number[-2:].isdigit()


def test_build_quotation_data_combines_process_and_pdf_specs() -> None:
    proceso = Proceso(
        codigo_necesidad="NIC-001",
        nombre_entidad="Ministerio de Prueba",
        fecha_publicacion=date(2026, 6, 8),
        fecha_limite=date(2026, 6, 10),
    )
    proceso.funcionario = Funcionario(nombre="Ana Perez", correo="ana@example.com")
    proceso.lugar_entrega = LugarEntrega(provincia="Pichincha", canton="Quito", direccion="Av. Siempre Viva")
    proceso.items_compra = [
        ItemCompra(
            numero=1,
            cpc="481200102",
            descripcion_producto="Cepillo de limpieza",
            unidad="Unidad",
            cantidad=Decimal("2"),
        )
    ]
    specs = EspecificacionPDF(
        plazo_ejecucion="30 dias",
        garantia="12 meses",
        validez_proforma="60 dias",
        terminos_condiciones="Entrega contra orden de compra.",
    )
    settings = SimpleNamespace(
        company_name="PINPREXAT",
        company_ruc="1790000000001",
        company_address="Quito",
        company_phone="0999999999",
        company_email="ventas@example.com",
    )

    data = build_quotation_data(
        proceso=proceso,
        specs=specs,
        settings=settings,
        numero_cotizacion="20260642",
        today=date(2026, 6, 8),
    )

    assert data.numero_cotizacion == "20260642"
    assert data.client.nombre == "Ministerio de Prueba"
    assert data.items[0].descripcion == "Cepillo de limpieza"
    assert data.plazo_ejecucion == "30 dias"
    assert data.fecha_publicacion == date(2026, 6, 8)
    assert data.fecha_limite_entrega == date(2026, 6, 10)


def test_render_quotation_pdf_creates_file(tmp_path) -> None:
    pytest.importorskip("reportlab")

    proceso = Proceso(codigo_necesidad="NIC-001", nombre_entidad="Ministerio de Prueba")
    settings = SimpleNamespace(
        company_name="PINPREXAT",
        company_ruc=None,
        company_address=None,
        company_phone=None,
        company_email=None,
    )
    data = build_quotation_data(
        proceso=proceso,
        specs=None,
        settings=settings,
        numero_cotizacion="20260642",
        today=date(2026, 6, 8),
    )

    pdf_path = render_quotation_pdf(data, tmp_path)

    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")
