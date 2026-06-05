# TICKET-006 - Fase 5: Scheduler y flujo principal

## Estado
Implementado inicial.

## Objetivo
Orquestar lectura de URLs, scraping, parsing, persistencia, logs y notificaciones.

## Cambios realizados
- `scheduler/job_runner.py`:
  - Lee `urls/targets.txt`.
  - Ignora duplicados y comentarios.
  - Ejecuta scraping por URL.
  - Guarda resultados en base de datos.
  - Registra ejecuciones.
  - Notifica nuevos procesos, cambios y errores.
  - Programa ejecuciones con APScheduler.
- `main.py`:
  - Ejecuta scheduler por defecto.
  - Permite ejecucion manual con `python main.py --once`.

## Validacion
- Compilacion de sintaxis.

## Pendiente relacionado
- Ejecutar `python main.py --once` con `.env`, PostgreSQL, Firecrawl y URLs reales.
