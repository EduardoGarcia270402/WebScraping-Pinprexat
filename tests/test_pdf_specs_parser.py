from parser.pdf_specs_parser import extract_specs_from_text


def test_extract_specs_from_text_finds_required_terms() -> None:
    text = """
    Plazo de ejecucion: 30 dias calendario contados desde la notificacion.
    Garantia tecnica: 12 meses contra defectos de fabricacion.
    Validez de la proforma: 60 dias.

    Terminos y condiciones:
    La entrega se realizara en las bodegas de la entidad contratante.

    Forma de pago:
    Contra entrega.
    """

    result = extract_specs_from_text(text)

    assert result["plazo_ejecucion"] == "30 dias calendario contados desde la notificacion"
    assert result["garantia"] == "12 meses contra defectos de fabricacion"
    assert result["validez_proforma"] == "60 dias"
    assert result["terminos_condiciones"] == "La entrega se realizara en las bodegas de la entidad contratante"


def test_extract_specs_from_text_handles_plural_uppercase_guarantee_and_offer_validity() -> None:
    text = """
    GARANTIAS
    El oferente debera presentar garantia minima de 6 meses por defectos de fabrica.

    VALIDEZ DE OFERTA
    minimo 30 dias calendario desde la presentacion de la proforma.
    """

    result = extract_specs_from_text(text)

    assert result["garantia"] == "minima de 6 meses por defectos de fabrica"
    assert result["validez_proforma"] == "minimo 30 dias calendario desde la presentacion de la proforma"


def test_extract_specs_from_numbered_sections_summarizes_exact_conditions() -> None:
    text = """
    12. GARANTIAS
    Otorgar una carta garantia minima de seis (6) meses sobre el servicio brindado,
    contados a partir de la fecha de recepcion a satisfaccion por el administrador de
    la orden de compra. Durante este periodo, el proveedor se compromete a subsanar.

    13. MULTAS
    Se aplicaran multas conforme a la normativa vigente.

    14. VIGENCIA DE LA OFERTA
    La oferta estara vigente por 40 dias, contados a partir de la presentacion de esta,
    de conformidad a lo dispuesto en el articulo correspondiente.
    """

    result = extract_specs_from_text(text)

    assert result["garantia"] == "minima de seis (6) meses sobre el servicio brindado"
    assert result["validez_proforma"] == "40 dias, contados a partir de la presentacion de esta"


def test_extract_specs_from_pdf_text_when_guarantee_paragraph_precedes_heading() -> None:
    text = """
    Otorgar una carta garantia minima de seis (6) meses sobre el servicio brindado, contados a
    partir de la fecha de recepcion a satisfaccion por el administrador de la orden de compra.
    Durante este periodo, el proveedor se compromete a subsanar.

    12. GARANTIAS
    13. MULTAS
    En los casos de retrasos injustificados se aplicaran multas.
    """

    result = extract_specs_from_text(text)

    assert result["garantia"] == "minima de seis (6) meses sobre el servicio brindado"


def test_extract_specs_from_text_ignores_early_guarantee_without_duration() -> None:
    text = """
    En caso de trabajos defectuosos, se aplicara la garantia correspondiente establecida
    contractualmente. Todas las piezas seran entregadas como respaldo tecnico.

    Otorgar una carta garantia minima de seis (6) meses sobre el servicio brindado, contados a
    partir de la fecha de recepcion a satisfaccion por el administrador de la orden de compra.

    12. GARANTIAS
    13. MULTAS
    """

    result = extract_specs_from_text(text)

    assert result["garantia"] == "minima de seis (6) meses sobre el servicio brindado"
