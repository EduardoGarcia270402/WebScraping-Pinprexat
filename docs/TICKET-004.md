# TICKET-004 - Fase 3: Scraper y parser

## Estado
Implementado inicial.

## Objetivo
Conectar Firecrawl y extraer los campos definidos del detalle NCO.

## Cambios realizados
- `scraper/firecrawl_client.py` encapsula Firecrawl.
- `parser/nco_parser.py` extrae:
  - Datos del proceso.
  - Funcionario encargado.
  - Lugar de entrega.
  - Items de compra.
- `tests/test_parser.py` cubre un caso base con tabla markdown.

## Validacion
- Test unitario preparado para `pytest`.
- Compilacion de sintaxis.

## Pendiente relacionado
- Probar con HTML/markdown real devuelto por Firecrawl desde una URL SERCOP.
- Ajustar patrones del parser si el portal usa etiquetas distintas en produccion.
