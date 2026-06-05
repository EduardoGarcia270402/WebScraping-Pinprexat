from decimal import Decimal

from parser.nco_parser import parse_nco_detail


def test_parse_nco_detail_from_markdown_table() -> None:
    raw = """
| Nombre Entidad | Municipio de Prueba |
| Tipo de Necesidad | Compra publica |
| Codigo Necesidad de Contratacion | NCO-001 |
| Estado de la Necesidad | Publicada |
| Fecha de Publicacion | 05/06/2026 |
| Fecha Limite | 10/06/2026 |
| Nombre | Ana Perez |
| Correo Electronico | ana@example.com |
| Provincia | Pichincha |
| Canton | Quito |
| Parroquia | Centro Historico |
| Direccion | Calle 10 |

| No. | CPC | Unidad | Cantidad |
| --- | --- | --- | --- |
| 1 | 123456 | Unidad | 2,50 |
"""

    result = parse_nco_detail(raw)

    assert result["codigo_necesidad"] == "NCO-001"
    assert result["nombre_entidad"] == "Municipio de Prueba"
    assert result["fecha_publicacion"].isoformat() == "2026-06-05"
    assert result["fecha_limite"].isoformat() == "2026-06-10"
    assert result["funcionario"]["nombre"] == "Ana Perez"
    assert result["funcionario"]["correo"] == "ana@example.com"
    assert result["lugar_entrega"]["canton"] == "Quito"
    assert result["items_compra"] == [
        {
            "numero": 1,
            "cpc": "123456",
            "unidad": "Unidad",
            "cantidad": Decimal("2.50"),
        }
    ]
