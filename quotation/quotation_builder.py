from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from random import SystemRandom

from config.settings import Settings
from database.models import EspecificacionPDF, Proceso


@dataclass(frozen=True)
class CompanyInfo:
    nombre: str
    ruc: str | None
    direccion: str | None
    telefono: str | None
    email: str | None
    logo_path: Path | None


@dataclass(frozen=True)
class ClientInfo:
    nombre: str | None
    contacto: str | None
    correo: str | None
    direccion: str | None
    provincia: str | None
    canton: str | None


@dataclass(frozen=True)
class QuotationItem:
    numero: int | None
    codigo: str | None
    descripcion: str | None
    unidad: str | None
    cantidad: Decimal | None


@dataclass(frozen=True)
class QuotationData:
    numero_cotizacion: str
    fecha: date
    fecha_publicacion: date | None
    fecha_limite_entrega: date | None
    codigo_necesidad: str
    company: CompanyInfo
    client: ClientInfo
    items: list[QuotationItem]
    plazo_ejecucion: str | None
    garantia: str | None
    validez_proforma: str | None
    terminos_condiciones: str | None


def generate_quotation_number(today: date | None = None) -> str:
    current_date = today or date.today()
    random_suffix = SystemRandom().randint(0, 99)
    return f"{current_date:%Y%m}{random_suffix:02d}"


def build_quotation_data(
    proceso: Proceso,
    specs: EspecificacionPDF | None,
    settings: Settings,
    numero_cotizacion: str | None = None,
    today: date | None = None,
) -> QuotationData:
    current_date = today or date.today()
    funcionario = proceso.funcionario
    lugar = proceso.lugar_entrega

    return QuotationData(
        numero_cotizacion=numero_cotizacion or generate_quotation_number(current_date),
        fecha=current_date,
        fecha_publicacion=proceso.fecha_publicacion,
        fecha_limite_entrega=proceso.fecha_limite,
        codigo_necesidad=proceso.codigo_necesidad,
        company=CompanyInfo(
            nombre=settings.company_name,
            ruc=settings.company_ruc,
            direccion=settings.company_address,
            telefono=settings.company_phone,
            email=settings.company_email,
            logo_path=getattr(settings, "company_logo_path", None),
        ),
        client=ClientInfo(
            nombre=proceso.nombre_entidad,
            contacto=funcionario.nombre if funcionario else None,
            correo=funcionario.correo if funcionario else None,
            direccion=lugar.direccion if lugar else None,
            provincia=lugar.provincia if lugar else None,
            canton=lugar.canton if lugar else None,
        ),
        items=[
            QuotationItem(
                numero=item.numero,
                codigo=item.cpc,
                descripcion=item.descripcion_producto or item.categoria_cpc,
                unidad=item.unidad,
                cantidad=item.cantidad,
            )
            for item in sorted(proceso.items_compra, key=lambda item: item.numero or 0)
        ],
        plazo_ejecucion=specs.plazo_ejecucion if specs else None,
        garantia=specs.garantia if specs else None,
        validez_proforma=specs.validez_proforma if specs else None,
        terminos_condiciones=specs.terminos_condiciones if specs else None,
    )
