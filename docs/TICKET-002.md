# TICKET-002 - Fase 1: Configuracion base

## Estado
Implementado.

## Objetivo
Crear la base del proyecto Python para el scraper SERCOP.

## Cambios realizados
- Estructura de carpetas principal: `config`, `scraper`, `parser`, `database`, `notifier`, `scheduler`, `tests`, `urls`, `logs`.
- Archivo `.env.example` con las variables requeridas.
- Archivo `.gitignore` para credenciales, caches, entornos virtuales y logs.
- Archivo `requirements.txt` con dependencias del ticket de diseno.
- Archivo `config/settings.py` para centralizar configuracion desde `.env`.
- Archivo `main.py` como punto de entrada.

## Validacion
- Compilacion de sintaxis con Python 3.12.13 del runtime de Codex.

## Pendiente relacionado
- Crear un `.env` local con credenciales reales antes de ejecutar contra Firecrawl/PostgreSQL.
