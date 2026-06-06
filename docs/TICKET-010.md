# TICKET-010 - Extraccion completa de items de compra

## Estado
Implementado y validado.

## Objetivo
Corregir la extraccion y almacenamiento del apartado `Detalle del objeto de compra` en paginas NCO de SERCOP, incluyendo todos los datos visibles de la tabla real.

## Problema detectado
- La tabla `items_compra` quedaba vacia despues de procesar la URL configurada en `urls/targets.txt`.
- El parser inicial esperaba una tabla simple de 4 columnas: `No.`, `CPC`, `Unidad`, `Cantidad`.
- La tabla real de SERCOP contiene mas columnas: `No.`, codigo `CPC`, categoria CPC, `Descripcion del Producto`, `Unidad` y `Cantidad`.
- Firecrawl podia devolver `markdown` y `html`, pero el cliente tomaba primero `markdown`; para esta tabla el HTML real resulto mas confiable.

## Cambios realizados
- `scraper/firecrawl_client.py` ahora prefiere contenido `html` antes que `markdown` cuando ambos estan disponibles.
- `parser/nco_parser.py` ahora parsea filas HTML (`tr` / `td` / `th`) antes de usar el fallback de texto.
- `parser/nco_parser.py` extrae por item:
  - `numero`
  - `cpc`
  - `categoria_cpc`
  - `descripcion_producto`
  - `unidad`
  - `cantidad`
- `database/models.py` agrego los campos ORM:
  - `categoria_cpc`
  - `descripcion_producto`
- `database/repository.py` incluyo los nuevos campos dentro de `ITEM_FIELDS` para crear, comparar y actualizar items.
- `database/schema.sql` incluyo las columnas nuevas en la definicion de `items_compra`.
- `database/queries.sql` actualizo la consulta de items para mostrar categoria y descripcion.
- `tests/test_parser.py` agrego una prueba con estructura HTML similar a la tabla real de SERCOP.
- `tests/test_firecrawl_client.py` agrego pruebas para asegurar que se use HTML cuando Firecrawl lo entrega.

## Cambio aplicado en PostgreSQL
Se ejecutaron los siguientes cambios sobre la base local:

```sql
ALTER TABLE items_compra
ADD COLUMN IF NOT EXISTS categoria_cpc VARCHAR;

ALTER TABLE items_compra
ADD COLUMN IF NOT EXISTS descripcion_producto TEXT;
```

## Validacion realizada
- Se proceso la URL real configurada en `urls/targets.txt`.
- El parser extrajo `17` items.
- `save_proceso` actualizo el proceso existente y detecto cambios en `items_compra`.
- Consulta final en PostgreSQL confirmo `17` filas guardadas en `items_compra`.
- Las nuevas columnas quedaron pobladas con datos reales.

Muestra confirmada en PostgreSQL:

```text
numero | cpc       | categoria_cpc       | descripcion_producto                                      | unidad | cantidad
1      | 481200102 | INSTRUMENTAL MEDICO | Cepillo de Limpieza para instrumentos rigidos 2mm...      | Unidad | 20.00
2      | 481200102 | INSTRUMENTAL MEDICO | Cepillo de Limpieza para instrumentos rigidos 3mm...      | Unidad | 20.00
3      | 481200102 | INSTRUMENTAL MEDICO | Cepillo de Limpieza para instrumentos rigidos 4mm...      | Unidad | 20.00
```

## Resultado de pruebas

```text
4 passed in 0.09s
```

## Pendiente / siguiente proceso
- Probar el mismo flujo con una nueva URL NCO para confirmar que la extraccion funciona con otros procesos.
- Si la siguiente pagina trae una estructura diferente, guardar respuesta cruda con `SAVE_RAW_RESPONSES=true` y ajustar el parser con ese HTML.
