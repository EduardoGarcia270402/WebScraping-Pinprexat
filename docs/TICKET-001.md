# SERCOP Scraper — Documento de Diseño

**Fecha:** 2026-06-05
**Stack principal:** Python
**Estado:** Aprobado

---

## 1. Descripción General

Sistema automatizado de web scraping para extraer información de procesos de contratación pública del portal SERCOP (compraspublicas.gob.ec). El sistema lee una lista de URLs, extrae campos específicos de cada proceso usando Firecrawl, almacena los datos en PostgreSQL y notifica por correo y Telegram ante nuevos registros, cambios o errores.

---

## 2. Objetivo

Extraer de páginas del tipo:
```
https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/NCORegistroDetalle.cpe?&id=<ID>&op=0
```

Los siguientes campos:

### Datos del Proceso
- Nombre Entidad
- Tipo de Necesidad
- Código Necesidad de Contratación *(clave única)*
- Estado de la Necesidad
- Fecha de Publicación
- Fecha Límite

### Funcionario Encargado
- Nombre
- Correo Electrónico

### Lugar de Entrega
- Provincia
- Cantón
- Parroquia
- Dirección

### Detalle del Objeto de Compra
- No.
- CPC
- Unidad
- Cantidad

---

## 3. Arquitectura de Carpetas

```
sercop-scraper/
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Variables de entorno, credenciales, URLs base
│
├── scraper/
│   ├── __init__.py
│   └── firecrawl_client.py      # Conexión y llamadas a Firecrawl API
│
├── parser/
│   ├── __init__.py
│   └── nco_parser.py            # Extrae los campos específicos del contenido crudo
│
├── database/
│   ├── __init__.py
│   ├── connection.py            # Conexión a PostgreSQL via SQLAlchemy
│   ├── models.py                # Definición de tablas (ORM)
│   └── repository.py           # Funciones CRUD: insertar, consultar, actualizar
│
├── notifier/
│   ├── __init__.py
│   ├── email_notifier.py        # Envío de correos via SMTP
│   └── telegram_notifier.py    # Envío de mensajes via Telegram Bot
│
├── scheduler/
│   ├── __init__.py
│   └── job_runner.py            # APScheduler — define frecuencia y orquesta el flujo
│
├── logs/
│   └── scraper.log              # Generado automáticamente por loguru
│
├── urls/
│   └── targets.txt              # Lista de URLs a scrapear (una por línea)
│
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-06-05-sercop-scraper-design.md
│
├── tests/
│   ├── test_parser.py
│   ├── test_database.py
│   └── test_notifier.py
│
├── .env                         # Credenciales reales (NO subir a git)
├── .env.example                 # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt
└── main.py                      # Punto de entrada — inicia el scheduler
```

### Responsabilidad de cada módulo

| Módulo | Responsabilidad |
|---|---|
| `config/settings.py` | Carga todas las variables de entorno con `python-dotenv`. Punto único de configuración. |
| `scraper/firecrawl_client.py` | Encapsula la API de Firecrawl. Recibe una URL, devuelve el contenido crudo (markdown/HTML). |
| `parser/nco_parser.py` | Recibe el contenido crudo y extrae los campos definidos. Devuelve un diccionario estructurado. |
| `database/connection.py` | Crea y gestiona la sesión de SQLAlchemy con PostgreSQL. |
| `database/models.py` | Define las tablas como clases ORM. |
| `database/repository.py` | Contiene las operaciones de base de datos: insertar proceso nuevo, actualizar existente, registrar ejecución. |
| `notifier/email_notifier.py` | Envía correos con `smtplib`. Recibe asunto y cuerpo del mensaje. |
| `notifier/telegram_notifier.py` | Envía mensajes con `python-telegram-bot`. |
| `scheduler/job_runner.py` | Define el job principal y lo programa con APScheduler para ejecutarse varias veces al día. |
| `urls/targets.txt` | Lista plana de URLs, una por línea. El usuario la edita manualmente. |
| `main.py` | Inicializa la base de datos y arranca el scheduler. |

---

## 4. Flujo de Datos

```
targets.txt
    │
    ▼
[scheduler/job_runner.py]
  APScheduler dispara el job X veces al día
    │
    ▼
[scraper/firecrawl_client.py]
  Lee cada URL de targets.txt
  Llama a Firecrawl API → devuelve contenido de la página
    │
    ▼
[parser/nco_parser.py]
  Extrae todos los campos definidos
  Devuelve diccionario estructurado
    │
    ▼
[database/repository.py]
  ¿Código Necesidad ya existe en DB?
  ├── NO  → INSERT nuevo registro
  ├── SÍ, sin cambios → solo log "sin cambios"
  └── SÍ, con cambios → UPDATE + notificación de cambio detectado
    │
    ├──► [notifier/email_notifier.py]
    └──► [notifier/telegram_notifier.py]
    │
    ▼
[logs/scraper.log]
  Registra cada ejecución con resultado
```

---

## 5. Modelo de Base de Datos (PostgreSQL)

### Tabla: `procesos`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | ID autoincremental |
| `codigo_necesidad` | VARCHAR UNIQUE NOT NULL | Clave única del proceso |
| `nombre_entidad` | VARCHAR | Nombre de la entidad pública |
| `tipo_necesidad` | VARCHAR | Tipo de contratación |
| `estado_necesidad` | VARCHAR | Estado actual del proceso |
| `fecha_publicacion` | DATE | Fecha de publicación |
| `fecha_limite` | DATE | Fecha límite |
| `creado_en` | TIMESTAMP | Cuándo se insertó |
| `actualizado_en` | TIMESTAMP | Última actualización |

### Tabla: `funcionarios`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | |
| `proceso_id` | FK → procesos.id | Relación al proceso |
| `nombre` | VARCHAR | Nombre del funcionario |
| `correo` | VARCHAR | Correo electrónico |

### Tabla: `lugares_entrega`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | |
| `proceso_id` | FK → procesos.id | Relación al proceso |
| `provincia` | VARCHAR | |
| `canton` | VARCHAR | |
| `parroquia` | VARCHAR | |
| `direccion` | TEXT | |

### Tabla: `items_compra`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | |
| `proceso_id` | FK → procesos.id | Relación al proceso |
| `numero` | INTEGER | No. del ítem |
| `cpc` | VARCHAR | Código CPC |
| `unidad` | VARCHAR | Unidad de medida |
| `cantidad` | DECIMAL | Cantidad requerida |

### Tabla: `ejecuciones_log`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | |
| `url` | TEXT | URL procesada |
| `estado` | VARCHAR | `exitoso` / `error` / `sin_cambios` |
| `mensaje` | TEXT | Detalle del resultado |
| `ejecutado_en` | TIMESTAMP | Cuándo corrió |

---

## 6. Stack Tecnológico

| Librería | Versión mínima | Uso |
|---|---|---|
| `firecrawl-py` | latest | Cliente oficial Firecrawl |
| `sqlalchemy` | 2.x | ORM para PostgreSQL |
| `psycopg2-binary` | 2.9+ | Driver PostgreSQL |
| `apscheduler` | 3.x | Scheduler de jobs |
| `python-dotenv` | 1.x | Lectura de variables de entorno |
| `python-telegram-bot` | 20.x | Bot de Telegram |
| `loguru` | 0.7+ | Logging con rotación automática |
| `pytest` | 7.x | Tests unitarios |
| `smtplib` | stdlib | Envío de correos (built-in) |

---

## 7. Manejo de Errores

| Situación | Comportamiento |
|---|---|
| Firecrawl no puede acceder a la URL | Log de error + notificación Email/Telegram + continúa con siguiente URL |
| Campo no encontrado en el parser | Guarda `NULL` en ese campo + warning en log |
| Error de conexión a PostgreSQL | Reintento 3 veces con espera progresiva, luego notificación crítica |
| URL duplicada en `targets.txt` | Se procesa una sola vez, la duplicada se ignora |
| Proceso existe en DB sin cambios | Solo registra en log como "sin_cambios", sin notificación |
| Proceso existe en DB con cambios | UPDATE del registro + notificación de cambio detectado |

---

## 8. Variables de Entorno (.env)

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sercop_db
DB_USER=postgres
DB_PASSWORD=tu_password

# Firecrawl
FIRECRAWL_API_KEY=tu_api_key

# Notificaciones - Email
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASSWORD=tu_app_password
EMAIL_DESTINATARIO=destinatario@gmail.com

# Notificaciones - Telegram
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id

# Scheduler (horas de ejecución, formato 24h separadas por coma)
SCHEDULE_HOURS=8,14,20
```

---

## 9. Fases de Implementación

### Fase 1 — Configuración base
- Crear estructura de carpetas y archivos vacíos
- Configurar `.env`, `.env.example`, `.gitignore`, `requirements.txt`
- Implementar `config/settings.py`

### Fase 2 — Base de datos
- Implementar `database/models.py` con las 4 tablas
- Implementar `database/connection.py`
- Implementar `database/repository.py` con operaciones CRUD

### Fase 3 — Scraper y Parser
- Implementar `scraper/firecrawl_client.py`
- Implementar `parser/nco_parser.py` con extracción de todos los campos

### Fase 4 — Notificaciones
- Implementar `notifier/email_notifier.py`
- Implementar `notifier/telegram_notifier.py`

### Fase 5 — Scheduler y punto de entrada
- Implementar `scheduler/job_runner.py` con APScheduler
- Implementar `main.py`

### Fase 6 — Tests
- Escribir `tests/test_parser.py`
- Escribir `tests/test_database.py`
- Escribir `tests/test_notifier.py`

---

## 10. Criterios de Éxito

- El scraper extrae correctamente los 14 campos definidos de una URL de prueba
- Los datos se persisten en PostgreSQL sin duplicados
- Los cambios en un proceso existente se detectan y actualizan
- Las notificaciones llegan correctamente por correo y Telegram
- El scheduler ejecuta el job a las horas configuradas sin intervención manual
- Los errores quedan registrados en log y generan notificación
