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
