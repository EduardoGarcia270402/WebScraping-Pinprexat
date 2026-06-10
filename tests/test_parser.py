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


def test_parse_nco_detail_from_real_publication_and_deadline_html() -> None:
    raw = """
<strong>Fecha de Publicación de la Necesidad:</strong>
<p class="card-text">2026-06-08 15:00:00</p>
<strong>Fecha Límite para la entrega de Proformas:</strong>
<p class="card-text">2026-06-10 15:00:00</p>
"""

    result = parse_nco_detail(raw)

    assert result["fecha_publicacion"].isoformat() == "2026-06-08"
    assert result["fecha_limite"].isoformat() == "2026-06-10"


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


def test_parse_documentos_from_terminos_referencia_section() -> None:
    raw = """
<div>ARCHIVO QUE CONTIENE LAS ESPECIFICACIONES TÉCNICAS / TÉRMINOS DE REFERENCIA</div>
<table>
    <tr>
        <th>Descripción del Archivo</th>
        <th>Descargar Archivo</th>
    </tr>
    <tr>
        <td>PROYECTOORDENDECOMPRA</td>
        <td><a href="../GE/descarga.cpe?archivo=orden"><img src="download.png"></a></td>
    </tr>
    <tr>
        <td>INFORMEDENECESIDAD</td>
        <td><a href="../GE/descarga.cpe?archivo=informe"><img src="download.png"></a></td>
    </tr>
    <tr>
        <td>TERMINOSDEREFERENCIA</td>
        <td><a href="../GE/descarga.cpe?archivo=tdr"><img src="download.png"></a></td>
    </tr>
</table>
"""

    result = parse_nco_detail(raw)

    assert result["documentos_anexos"] == [
        {
            "descripcion_archivo": "PROYECTOORDENDECOMPRA",
            "download_url": "../GE/descarga.cpe?archivo=orden",
        },
        {
            "descripcion_archivo": "INFORMEDENECESIDAD",
            "download_url": "../GE/descarga.cpe?archivo=informe",
        },
        {
            "descripcion_archivo": "TERMINOSDEREFERENCIA",
            "download_url": "../GE/descarga.cpe?archivo=tdr",
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
