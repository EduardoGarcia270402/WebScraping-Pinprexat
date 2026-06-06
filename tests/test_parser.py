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


def test_parse_nco_detail_from_sercop_html_item_table() -> None:
    raw = """
<h2 class="importante">Detalle del objeto de compra</h2>
<table class="table table-striped mt-4">
    <thead>
        <tr>
            <th>No.</th><th colspan="2">CPC</th><th>Descripci&oacute;n del Producto</th>
            <th>Unidad</th><th>Cantidad</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td><td>481200102</td><td>INSTRUMENTAL MEDICO</td>
            <td class="multiline-text">Cepillo de Limpieza 2mm</td>
            <td>Unidad</td><td>20.00</td>
        </tr>
        <tr>
            <td>2</td><td>481200102</td><td>INSTRUMENTAL MEDICO</td>
            <td class="multiline-text">Cepillo de Limpieza 3mm</td>
            <td>Unidad</td><td>40.00</td>
        </tr>
    </tbody>
</table>
"""

    result = parse_nco_detail(raw)

    assert result["items_compra"] == [
        {
            "numero": 1,
            "cpc": "481200102",
            "categoria_cpc": "INSTRUMENTAL MEDICO",
            "descripcion_producto": "Cepillo de Limpieza 2mm",
            "unidad": "Unidad",
            "cantidad": Decimal("20.00"),
        },
        {
            "numero": 2,
            "cpc": "481200102",
            "categoria_cpc": "INSTRUMENTAL MEDICO",
            "descripcion_producto": "Cepillo de Limpieza 3mm",
            "unidad": "Unidad",
            "cantidad": Decimal("40.00"),
        },
    ]


def test_parse_nco_detail_from_documentos_anexos() -> None:
    raw = """
<h2 class="importante mt-4">Documentos Anexos</h2>
<table>
    <tr>
        <td><b>Descripcion del Archivo</b></td>
        <td><b>Descargar Archivo</b></td>
    </tr>
    <tr>
        <td> modelo de orden </td>
        <td><a href="../GE/ExeGENBajarArchivoGeneral.cpe?Archivo=abc,&idPath=def,">
            <img src="../img/bajar.gif">
        </a></td>
    </tr>
    <tr>
        <td> ESPECIFICACIONES TECNICAS </td>
        <td><a href="../GE/ExeGENBajarArchivoGeneral.cpe?Archivo=ghi,&idPath=jkl,">
            <img src="../img/bajar.gif">
        </a></td>
    </tr>
</table>
"""

    result = parse_nco_detail(raw)

    assert result["documentos_anexos"] == [
        {
            "descripcion_archivo": "modelo de orden",
            "download_url": "../GE/ExeGENBajarArchivoGeneral.cpe?Archivo=abc,&idPath=def,",
        },
        {
            "descripcion_archivo": "ESPECIFICACIONES TECNICAS",
            "download_url": "../GE/ExeGENBajarArchivoGeneral.cpe?Archivo=ghi,&idPath=jkl,",
        },
    ]


def test_parse_nco_detail_from_proveedores_table() -> None:
    raw = """
<h2>Proveedores</h2>
<table>
    <tr><th>No.</th><th>RUC/ID</th><th>Razon Social</th></tr>
    <tr>
        <td>1</td><td>1793205498001</td>
        <td>COMERCIALIZADORA Y MANTENIMIENTO DE MAQUINARIA PESADA</td>
    </tr>
    <tr>
        <td>2</td><td>1802785681001</td>
        <td>SANTIN LASCANO ALFONSO LEONARDO</td>
    </tr>
</table>
"""

    result = parse_nco_detail(raw)

    assert result["proveedores"] == [
        {
            "numero": 1,
            "ruc_id": "1793205498001",
            "razon_social": "COMERCIALIZADORA Y MANTENIMIENTO DE MAQUINARIA PESADA",
        },
        {
            "numero": 2,
            "ruc_id": "1802785681001",
            "razon_social": "SANTIN LASCANO ALFONSO LEONARDO",
        },
    ]
