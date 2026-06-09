# TICKET-012 - Extraccion de PDF y generacion automatica de cotizaciones

## Estado
Implementado y validado.

## Objetivo
Agregar un nuevo proceso posterior al scraping para combinar los datos obtenidos desde SERCOP con datos extraidos del PDF de especificaciones tecnicas, generar automaticamente un documento PDF de cotizacion y subirlo a Google Drive en una carpeta separada para cotizaciones.

## Alcance implementado
- Extraccion de texto desde el PDF descargado de especificaciones tecnicas.
- Deteccion de campos clave dentro del PDF:
  - `plazo_ejecucion`
  - `garantia`
  - `validez_proforma`
  - `terminos_condiciones`
- Guardado de datos extraidos del PDF en base de datos.
- Generacion automatica de numero de cotizacion con formato `YYYYMM##`.
- Construccion de datos de cotizacion combinando:
  - datos de la empresa oferente desde `.env`
  - datos del cliente/proceso desde la base de datos
  - productos/items del proceso
  - condiciones extraidas desde el PDF
- Generacion local del PDF de cotizacion.
- Subida del PDF generado a Google Drive.
- Configuracion de carpeta Drive independiente para cotizaciones.

## Cambios realizados
- `parser/pdf_specs_parser.py` agregado para extraer texto y campos clave desde el PDF.
- `quotation/quotation_builder.py` agregado para construir el objeto de datos de la cotizacion.
- `quotation/pdf_renderer.py` agregado para generar el PDF de cotizacion con `reportlab`.
- `quotation/__init__.py` agregado para declarar el paquete de cotizaciones.
- `database/models.py` agrego los modelos:
  - `EspecificacionPDF`
  - `Cotizacion`
- `database/repository.py` agrego funciones para:
  - guardar especificaciones extraidas del PDF
  - guardar cotizaciones generadas
  - consultar cotizaciones existentes
  - evitar duplicados por numero de cotizacion
- `database/schema.sql` agrego las tablas:
  - `especificaciones_pdf`
  - `cotizaciones`
- `scheduler/job_runner.py` integro el nuevo flujo despues de guardar el proceso:
  - buscar PDF local descargado
  - extraer datos del PDF
  - guardar especificaciones
  - generar cotizacion
  - subir cotizacion a Drive si `DRIVE_UPLOAD_ENABLED=true`
- `config/settings.py` agrego configuracion para:
  - activar/desactivar cotizaciones
  - definir carpeta local de salida
  - definir carpeta Drive de cotizaciones
  - definir datos de la empresa oferente
- `.env.example` documento las nuevas variables.
- `.env` fue configurado con los datos reales del oferente y la carpeta Drive de cotizaciones.
- `requirements.txt` agrego:
  - `pypdf`
  - `reportlab`
- `tests/test_pdf_specs_parser.py` agrego prueba de extraccion de campos desde texto.
- `tests/test_quotation.py` agrego pruebas para:
  - formato de numero de cotizacion
  - combinacion de datos de proceso/PDF
  - generacion real de PDF local.

## Tablas agregadas

### `especificaciones_pdf`

```sql
CREATE TABLE IF NOT EXISTS especificaciones_pdf (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER UNIQUE NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    documento_anexo_id INTEGER REFERENCES documentos_anexos(id) ON DELETE SET NULL,
    plazo_ejecucion TEXT,
    garantia TEXT,
    validez_proforma TEXT,
    terminos_condiciones TEXT,
    texto_extraido TEXT,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### `cotizaciones`

```sql
CREATE TABLE IF NOT EXISTS cotizaciones (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    numero_cotizacion VARCHAR UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    ruta_pdf TEXT,
    drive_file_id VARCHAR,
    drive_url TEXT,
    estado VARCHAR NOT NULL DEFAULT 'generada',
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Configuracion agregada

Variables nuevas en `.env`:

```env
QUOTATION_ENABLED=true
QUOTATIONS_DIR=downloads/cotizaciones
QUOTATION_DRIVE_FOLDER_ID=1DMYOlHKpN9NeXaeqdRwOu7ku5YdwOPCI
QUOTATION_DRIVE_FOLDER_NAME=Cotizaciones

COMPANY_NAME=PINPREXAT EXACTITUD SOPORTE Y AUTOMATIZACION CIA. LTDA
COMPANY_RUC=1792428467001
COMPANY_ADDRESS=Av. Puerto Rico s2-227 / Quito-Ecuador
COMPANY_PHONE=593 991651519 / 593 22869270
COMPANY_EMAIL=gianpinto.biz@gmail.com
```

La subida a Drive sigue dependiendo de la configuracion OAuth existente:

```env
DRIVE_UPLOAD_ENABLED=true
DRIVE_AUTH_MODE=oauth
DRIVE_OAUTH_CLIENT_FILE=credentials/google-drive-oauth-client.json
DRIVE_OAUTH_TOKEN_FILE=credentials/google-drive-token.json
```

## Flujo final implementado

```text
Scraping SERCOP
-> parseo de datos del proceso
-> descarga del PDF de especificaciones tecnicas
-> subida del PDF original a Drive
-> guardado del proceso en base de datos
-> extraccion de datos desde el PDF
-> guardado de especificaciones_pdf
-> generacion del PDF de cotizacion
-> subida de cotizacion a Drive carpeta Cotizaciones
-> guardado de cotizaciones en base de datos
```

## Validacion realizada
- Se instalaron las dependencias nuevas con `pip install -r requirements.txt`.
- Se ejecuto la suite de pruebas completa.
- Se valido la generacion real de un PDF local con `reportlab`.
- Se configuro la carpeta Drive `Cotizaciones` usando el ID entregado por el usuario.
- Se ejecuto la prueba real del flujo y la cotizacion generada se subio correctamente a Google Drive.

## Resultado de pruebas

```text
14 passed in 0.99s
```

## Notas importantes
- Si un proceso ya tiene una cotizacion registrada en `cotizaciones`, el flujo no genera otra automaticamente para evitar duplicados.
- La carpeta local de salida es `downloads/cotizaciones`.
- La carpeta Drive de destino para cotizaciones es independiente de la carpeta usada para anexos.
- Si `QUOTATION_DRIVE_FOLDER_ID` esta configurado, se usa directamente esa carpeta.
- Si `QUOTATION_DRIVE_FOLDER_ID` esta vacio, el sistema busca o crea una carpeta con nombre `QUOTATION_DRIVE_FOLDER_NAME`.
- Si falla la extraccion del PDF, el scraper no se detiene; registra un warning y puede generar una cotizacion con los datos disponibles.
- Si falla la generacion o subida de la cotizacion, el proceso principal de scraping continua y registra el error en logs.

## Pendiente / siguiente proceso
- Pulir el diseno visual de la cotizacion PDF.
- Definir de donde saldran precios unitarios, subtotal, IVA y total.
- Agregar forma de pago y condiciones comerciales definitivas.
- Evaluar regeneracion controlada de cotizaciones cuando cambien productos, condiciones o PDF.
- Mejorar los patrones de extraccion si aparecen PDFs con formatos diferentes o escaneados.
