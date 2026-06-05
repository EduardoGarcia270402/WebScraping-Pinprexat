# TICKET-005 - Fase 4: Notificaciones

## Estado
Implementado inicial.

## Objetivo
Enviar avisos cuando haya procesos nuevos, cambios o errores.

## Cambios realizados
- `notifier/email_notifier.py` envia correos por SMTP.
- `notifier/telegram_notifier.py` envia mensajes usando `python-telegram-bot`.
- Las funciones retornan `False` si faltan credenciales para no romper ejecuciones locales incompletas.
- `NOTIFICATIONS_ENABLED=false` permite ejecutar pruebas sin enviar email ni Telegram.

## Validacion
- Compilacion de sintaxis.

## Pendiente relacionado
- Validar SMTP con password de aplicacion.
- Validar Telegram con bot token y chat id reales.
- Cambiar `NOTIFICATIONS_ENABLED=true` cuando se quiera probar notificaciones.
