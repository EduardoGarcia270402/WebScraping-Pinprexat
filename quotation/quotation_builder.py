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
    precio_unitario: Decimal | None
    monto_total: Decimal | None


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

    @property
    def subtotal(self) -> Decimal:
        return sum(
            (item.monto_total or Decimal("0") for item in self.items),
            start=Decimal("0"),
        )


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
    item_values: list[dict[str, object]] | None = None,
    overrides: dict[str, str | None] | None = None,
) -> QuotationData:
    current_date = today or date.today()
    funcionario = proceso.funcionario
    lugar = proceso.lugar_entrega
    values_by_number = {
        int(value["numero"]): value
        for value in item_values or []
        if value.get("numero") is not None
    }
    overrides = overrides or {}

    items = []
    for item in sorted(proceso.items_compra, key=lambda current: current.numero or 0):
        item_value = values_by_number.get(item.numero or 0, {})
        items.append(
            QuotationItem(
                numero=item.numero,
                codigo=str(item_value.get("codigo") or item.cpc or "") or None,
                descripcion=str(
                    item_value.get("descripcion")
                    or item.descripcion_producto
                    or item.categoria_cpc
                    or ""
                ) or None,
                unidad=str(item_value.get("unidad") or item.unidad or "") or None,
                cantidad=_decimal_or_none(item_value.get("cantidad", item.cantidad)),
                precio_unitario=_decimal_or_none(item_value.get("precio_unitario")),
                monto_total=_decimal_or_none(item_value.get("monto_total")),
            )
        )

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
            nombre=overrides.get("cliente_nombre", proceso.nombre_entidad),
            contacto=overrides.get("contacto", funcionario.nombre if funcionario else None),
            correo=overrides.get("correo", funcionario.correo if funcionario else None),
            direccion=overrides.get("direccion", lugar.direccion if lugar else None),
            provincia=overrides.get("provincia", lugar.provincia if lugar else None),
            canton=overrides.get("canton", lugar.canton if lugar else None),
        ),
        items=items,
        plazo_ejecucion=overrides.get("plazo_ejecucion", specs.plazo_ejecucion if specs else None),
        garantia=overrides.get("garantia", specs.garantia if specs else None),
        validez_proforma=overrides.get("validez_proforma", specs.validez_proforma if specs else None),
        terminos_condiciones=overrides.get(
            "terminos_condiciones",
            specs.terminos_condiciones if specs else None,
        ),
    )


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))
