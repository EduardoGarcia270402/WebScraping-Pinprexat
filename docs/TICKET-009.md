# TICKET-009 - Consulta de datos guardados

## Estado
Implementado inicial.

## Objetivo
Facilitar la revision de los datos extraidos y almacenados en PostgreSQL.

## Hallazgos
- La ejecucion registro `sin_cambios`, lo que indica que el proceso ya existia en base de datos.
- Firecrawl entrego algunos valores con marcas markdown `**`.
- La pagina procesada guardo datos de proceso, funcionario y lugar de entrega.
- No se guardaron items de compra en la primera prueba; se requiere revisar el markdown/HTML real de Firecrawl para ajustar esa parte del parser.

## Cambios realizados
- `parser/nco_parser.py` limpia marcas markdown comunes en valores extraidos.
- `database/queries.sql` contiene consultas utiles para revisar procesos, funcionario, lugar, items y ejecuciones.
- `SAVE_RAW_RESPONSES=true` permite guardar el contenido crudo de Firecrawl en `logs/raw/` para depurar el parser.

## Validacion realizada
Se consultaron las tablas `procesos`, `funcionarios`, `lugares_entrega`, `items_compra` y `ejecuciones_log` con `psql`.
