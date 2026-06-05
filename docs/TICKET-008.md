# TICKET-008 - Inicializacion local de PostgreSQL

## Estado
Implementado.

## Objetivo
Preparar la base local para ejecutar el scraper contra PostgreSQL instalado en la maquina.

## Hallazgos
- PostgreSQL 18 esta instalado en `C:\Program Files\PostgreSQL\18`.
- El servicio `postgresql-x64-18` esta corriendo.
- `psql.exe` existe, pero no esta agregado al `PATH` de esta terminal.
- La conexion con el usuario `postgres` fue validada.
- La base `sercop_db` fue creada.
- Las tablas del proyecto fueron creadas en `sercop_db`.

## Cambios realizados
- `database/connection.py` ahora incluye `check_db_connection()`.
- `scripts/init_db.py` valida conexion, crea tablas con SQLAlchemy y lista las tablas disponibles.
- `database/schema.sql` permite crear las tablas directamente con `psql`.

## Pasos manuales requeridos
1. Mantener `DB_PASSWORD` actualizado en `.env`.
2. Ejecutar `python -m scripts.init_db` cuando el entorno Python local tenga dependencias instaladas.
3. Usar `database/schema.sql` como respaldo manual para recrear tablas con `psql`.

## Tablas esperadas
- `procesos`
- `funcionarios`
- `lugares_entrega`
- `items_compra`
- `ejecuciones_log`

## Validacion realizada
Consulta ejecutada en PostgreSQL:

```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

Resultado:

- `ejecuciones_log`
- `funcionarios`
- `items_compra`
- `lugares_entrega`
- `procesos`
