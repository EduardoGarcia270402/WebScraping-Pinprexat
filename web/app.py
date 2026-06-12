from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, flash, redirect, render_template, request, send_file, url_for

from config.settings import get_settings
from database.connection import SessionLocal, init_db
from database.repository import (
    get_cotizacion_by_id,
    get_cotizacion_by_numero,
    get_proceso_by_id,
    save_cotizacion,
    save_proceso,
)
from parser.nco_parser import parse_nco_detail
from quotation.pdf_renderer import render_quotation_pdf
from quotation.quotation_builder import build_quotation_data, generate_quotation_number
from scheduler.job_runner import _extract_and_save_specs, _process_documentos_anexos
from scraper.drive_uploader import upload_to_drive
from scraper.firecrawl_client import FirecrawlScraper


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "pinprexat-local-quotation-ui"

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/cargar")
    def load_url():
        source_url = request.form.get("url", "").strip()
        if not _is_http_url(source_url):
            flash("Ingresa una URL valida de SERCOP.", "error")
            return redirect(url_for("index"))

        try:
            raw_content = FirecrawlScraper().scrape(source_url)
            parsed = parse_nco_detail(raw_content)
            if not parsed.get("codigo_necesidad"):
                raise ValueError("No se encontro el codigo de necesidad en la pagina.")

            _process_documentos_anexos(source_url, parsed)
            with SessionLocal() as session:
                result = save_proceso(session, parsed)
                session.flush()
                _extract_and_save_specs(session, result.proceso)
                proceso_id = result.proceso.id
                session.commit()
        except Exception as exc:
            flash(f"No se pudo cargar la cotizacion: {exc}", "error")
            return redirect(url_for("index"))

        return redirect(url_for("edit_quotation", proceso_id=proceso_id))

    @app.get("/cotizaciones/nueva/<int:proceso_id>")
    def edit_quotation(proceso_id: int):
        with SessionLocal() as session:
            proceso = get_proceso_by_id(session, proceso_id)
            if proceso is None:
                abort(404)
            return render_template("quotation_form.html", proceso=proceso)

    @app.post("/cotizaciones/generar/<int:proceso_id>")
    def generate_quotation(proceso_id: int):
        settings = get_settings()
        try:
            with SessionLocal() as session:
                proceso = get_proceso_by_id(session, proceso_id)
                if proceso is None:
                    abort(404)

                item_values = _parse_item_values(proceso.items_compra)
                quotation_data = build_quotation_data(
                    proceso=proceso,
                    specs=proceso.especificaciones_pdf,
                    settings=settings,
                    numero_cotizacion=_unique_quotation_number(session),
                    item_values=item_values,
                    overrides=_parse_overrides(),
                )
                pdf_path = render_quotation_pdf(quotation_data, settings.quotations_dir)
                cotizacion_data = {
                    "numero_cotizacion": quotation_data.numero_cotizacion,
                    "fecha": quotation_data.fecha,
                    "ruta_pdf": str(pdf_path),
                    "subtotal": quotation_data.subtotal,
                    "estado": "generada",
                    "items": [
                        {
                            "numero": item.numero,
                            "codigo": item.codigo,
                            "descripcion": item.descripcion,
                            "unidad": item.unidad,
                            "cantidad": item.cantidad,
                            "precio_unitario": item.precio_unitario,
                            "monto_total": item.monto_total,
                        }
                        for item in quotation_data.items
                    ],
                }

                if settings.drive_upload_enabled:
                    cotizacion_data.update(_upload_quotation(pdf_path, settings))

                cotizacion = save_cotizacion(session, proceso, cotizacion_data)
                session.commit()
                cotizacion_id = cotizacion.id
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("edit_quotation", proceso_id=proceso_id))
        except Exception as exc:
            flash(f"No se pudo generar la cotizacion: {exc}", "error")
            return redirect(url_for("edit_quotation", proceso_id=proceso_id))

        return redirect(url_for("quotation_ready", cotizacion_id=cotizacion_id))

    @app.get("/cotizaciones/<int:cotizacion_id>")
    def quotation_ready(cotizacion_id: int):
        with SessionLocal() as session:
            cotizacion = get_cotizacion_by_id(session, cotizacion_id)
            if cotizacion is None:
                abort(404)
            return render_template("quotation_ready.html", cotizacion=cotizacion)

    @app.get("/cotizaciones/<int:cotizacion_id>/pdf")
    def download_quotation(cotizacion_id: int):
        with SessionLocal() as session:
            cotizacion = get_cotizacion_by_id(session, cotizacion_id)
            if cotizacion is None or not cotizacion.ruta_pdf:
                abort(404)
            pdf_path = Path(cotizacion.ruta_pdf)
            if not pdf_path.exists():
                abort(404)
            return send_file(pdf_path, as_attachment=False)

    return app


def run_web_app() -> None:
    init_db()
    create_app().run(host="127.0.0.1", port=5000, debug=False)


def _parse_item_values(items) -> list[dict[str, object]]:
    parsed = []
    for item in items:
        price = _required_money(request.form.get(f"precio_unitario_{item.id}"), "precio unitario")
        total = _required_money(request.form.get(f"monto_total_{item.id}"), "monto total")
        parsed.append(
            {
                "numero": item.numero,
                "codigo": request.form.get(f"codigo_{item.id}", "").strip(),
                "descripcion": request.form.get(f"descripcion_{item.id}", "").strip(),
                "unidad": request.form.get(f"unidad_{item.id}", "").strip(),
                "cantidad": _required_non_negative_decimal(
                    request.form.get(f"cantidad_{item.id}"),
                    "cantidad",
                ),
                "precio_unitario": price,
                "monto_total": total,
            }
        )
    if not parsed:
        raise ValueError("La cotizacion no contiene productos.")
    return parsed


def _parse_overrides() -> dict[str, str | None]:
    fields = (
        "cliente_nombre",
        "contacto",
        "correo",
        "direccion",
        "provincia",
        "canton",
        "plazo_ejecucion",
        "garantia",
        "validez_proforma",
        "terminos_condiciones",
    )
    return {field: request.form.get(field, "").strip() or None for field in fields}


def _required_money(value: str | None, label: str) -> Decimal:
    return _required_non_negative_decimal(value, label).quantize(Decimal("0.01"))


def _required_decimal(value: str | None, label: str) -> Decimal:
    try:
        return Decimal((value or "").replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"Ingresa un valor valido para {label}.") from exc


def _required_non_negative_decimal(value: str | None, label: str) -> Decimal:
    amount = _required_decimal(value, label)
    if amount < 0:
        raise ValueError(f"El {label} no puede ser negativo.")
    return amount


def _unique_quotation_number(session) -> str:
    for _ in range(20):
        number = generate_quotation_number()
        if get_cotizacion_by_numero(session, number) is None:
            return number
    raise RuntimeError("No se pudo generar un numero de cotizacion unico.")


def _upload_quotation(pdf_path: Path, settings) -> dict[str, str]:
    credentials_file = (
        settings.drive_oauth_client_file
        if settings.drive_auth_mode == "oauth"
        else settings.drive_service_account_file
    )
    if credentials_file is None:
        raise ValueError("Faltan las credenciales de Google Drive.")
    return upload_to_drive(
        local_path=pdf_path,
        credentials_file=credentials_file,
        folder_name=settings.quotation_drive_folder_name,
        folder_id=settings.quotation_drive_folder_id,
        auth_mode=settings.drive_auth_mode,
        token_file=settings.drive_oauth_token_file,
    )


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
