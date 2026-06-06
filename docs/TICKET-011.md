# TICKET-011 - Documentos anexos, proveedores y subida a Google Drive

## Estado
Implementado y validado.

## Objetivo
Ampliar el scraper NCO para extraer proveedores, registrar documentos anexos, descargar los archivos relacionados al proceso y subirlos a Google Drive con nombres asociados al codigo de necesidad de contratacion.

## Alcance implementado
- Extraccion de la seccion `Proveedores`.
- Creacion de tabla `proveedores`.
- Extraccion de la seccion `Documentos Anexos`.
- Creacion de tabla `documentos_anexos`.
- Descarga local de archivos anexos.
- Renombrado de archivos con referencia al codigo de necesidad.
- Subida a Google Drive en la carpeta `NecesidadesContratacion`.
- Guardado en base de datos de ruta local, nombre de archivo y enlace/ID de Drive.

## Cambios realizados
- `parser/nco_parser.py` ahora extrae:
  - `proveedores`
  - `documentos_anexos`
- `database/models.py` agrego los modelos:
  - `Proveedor`
  - `DocumentoAnexo`
- `database/repository.py` guarda y actualiza proveedores y documentos anexos junto con el proceso.
- `database/schema.sql` agrego las tablas `proveedores` y `documentos_anexos`.
- `database/queries.sql` agrego consultas para revisar proveedores y anexos guardados.
- `scraper/document_downloader.py` descarga anexos y genera nombres de archivo usando el codigo NIC.
- `scraper/drive_uploader.py` sube archivos a Google Drive.
- `scheduler/job_runner.py` procesa documentos anexos despues del parseo y antes de guardar el proceso.
- `.env.example` documento las variables nuevas de descarga y Drive.
- `.gitignore` ignora `credentials/` y `downloads/` para no subir credenciales ni archivos descargados.
- `requirements.txt` agrego dependencias de Google Drive y OAuth.

## Tablas agregadas

### `proveedores`

```sql
CREATE TABLE IF NOT EXISTS proveedores (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    numero INTEGER,
    ruc_id VARCHAR,
    razon_social TEXT
);
```

### `documentos_anexos`

```sql
CREATE TABLE IF NOT EXISTS documentos_anexos (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    descripcion_archivo TEXT,
    download_url TEXT,
    nombre_archivo VARCHAR,
    ruta_local TEXT,
    drive_file_id VARCHAR,
    drive_url TEXT
);
```

## Configuracion Drive
Se descarto usar `service_account` para carpetas normales de Drive personal porque Google devuelve:

```text
Service Accounts do not have storage quota
```

Se cambio a OAuth de usuario:

```env
DRIVE_UPLOAD_ENABLED=true
DRIVE_AUTH_MODE=oauth
DRIVE_FOLDER_ID=1WWdWvs9mnGqSsqq8JscJ064FBRHgej-y
DRIVE_FOLDER_NAME=NecesidadesContratacion
DRIVE_OAUTH_CLIENT_FILE=credentials/google-drive-oauth-client.json
DRIVE_OAUTH_TOKEN_FILE=credentials/google-drive-token.json
```

Archivos locales de credenciales:

```text
credentials/google-drive-oauth-client.json
credentials/google-drive-token.json
```

Estos archivos no deben subirse al repositorio. Quedan ignorados por:

```gitignore
credentials/
```

## Validacion realizada
- Se ejecuto `python main.py --once`.
- Se abrio el flujo de autorizacion de Google.
- Se agrego el usuario como tester en Google Auth Platform.
- Se genero `credentials/google-drive-token.json`.
- Los documentos anexos se descargaron localmente en `downloads/documentos_anexos`.
- Los documentos se subieron correctamente a la carpeta de Drive `NecesidadesContratacion`.

## Resultado de pruebas

```text
6 passed
```

## Notas importantes
- La primera ejecucion con OAuth abre navegador para autorizar la cuenta de Google.
- Las siguientes ejecuciones usan `google-drive-token.json`.
- Si se borra el token, el scraper volvera a pedir autorizacion.
- Si una URL no contiene seccion `Proveedores`, la tabla queda sin registros para ese proceso.
- Si una URL contiene proveedores, el parser ya esta preparado para guardar `numero`, `ruc_id` y `razon_social`.

## Pendiente / siguiente proceso
- Probar con una URL NCO que incluya tabla `Proveedores` visible para validar insercion real en `proveedores`.
- Revisar si se requiere conservar versiones anteriores de archivos en Drive o reemplazar archivos con el mismo nombre.
