# TICKET-003 - Fase 2: Base de datos

## Estado
Implementado inicial.

## Objetivo
Modelar la persistencia de procesos SERCOP y preparar operaciones CRUD principales.

## Cambios realizados
- `database/models.py` define tablas ORM:
  - `procesos`
  - `funcionarios`
  - `lugares_entrega`
  - `items_compra`
  - `ejecuciones_log`
- `database/connection.py` crea engine, sesiones e inicializacion de tablas.
- `database/repository.py` permite:
  - Buscar proceso por `codigo_necesidad`.
  - Guardar proceso nuevo.
  - Actualizar proceso existente si hay cambios.
  - Detectar `sin_cambios`.
  - Registrar ejecuciones.

## Validacion
- Compilacion de sintaxis.

## Pendiente relacionado
- Validar contra PostgreSQL real cuando existan credenciales locales.
- Agregar migraciones si el proyecto crece mas alla de `Base.metadata.create_all`.
