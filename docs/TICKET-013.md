# TICKET-013 - Frontend para revision y precios de cotizaciones

## Objetivo

Permitir que la persona encargada cargue una URL de SERCOP, revise los datos obtenidos,
ingrese precios variables y genere la cotizacion solamente despues de confirmar la
informacion.

## Flujo implementado

```text
Ingresar URL
-> scraping y descarga del anexo
-> carga de datos del proceso
-> revision y edicion de cliente, productos y condiciones
-> ingreso de precio unitario y monto total por producto
-> generacion manual del PDF
-> guardado de precios en base de datos
-> subida opcional a Google Drive
```

## Manejo de enlaces

Los enlaces ingresados desde el frontend **no se guardan automaticamente** en
`urls/targets.txt`.

Existen dos flujos separados:

### Frontend web

Cuando el encargado ingresa un enlace en la pantalla:

```text
Formulario web
-> procesamiento inmediato de ese enlace
-> carga del formulario de cotizacion
-> revision e ingreso de precios
-> generacion manual del PDF
```

El enlace se utiliza una sola vez para preparar la cotizacion. No se agrega al archivo
de monitoreo y no se vuelve a procesar por el scheduler, a menos que tambien se agregue
manualmente a `urls/targets.txt`.

### Archivo `urls/targets.txt`

Este archivo contiene los enlaces que deben ser procesados por el flujo ejecutado desde
la terminal:

```powershell
python main.py --once
```

Tambien es utilizado cuando se inicia el scheduler:

```powershell
python main.py
```

Por lo tanto, el enlace que actualmente permanece en `urls/targets.txt` se conserva y
solo sera procesado cuando se ejecute uno de esos dos comandos. Iniciar o utilizar el
frontend con `python main.py --web` no procesa automaticamente los enlaces del archivo.

### Decision de diseno

Se mantiene esta separacion para evitar que cada enlace usado para una cotizacion manual
quede registrado como objetivo permanente del scheduler. Si un proceso necesita
monitoreo recurrente, su enlace debe agregarse expresamente a `urls/targets.txt`.

## Ejecucion

Instalar las dependencias y levantar la interfaz:

```powershell
pip install -r requirements.txt
python main.py --web
```

Abrir `http://127.0.0.1:5000`.

## Configuracion

La generacion automatica queda desactivada por defecto:

```env
QUOTATION_ENABLED=true
QUOTATION_AUTO_GENERATE=false
```

El scheduler puede seguir recopilando y actualizando procesos, pero la cotizacion se
genera desde la interfaz despues de completar los precios.

Resumen de modos:

| Comando | Fuente de enlaces | Generacion de cotizacion |
| --- | --- | --- |
| `python main.py --web` | Enlace ingresado en la pantalla | Manual, despues de revisar precios |
| `python main.py --once` | `urls/targets.txt` | Depende de `QUOTATION_AUTO_GENERATE` |
| `python main.py` | `urls/targets.txt`, segun horario | Depende de `QUOTATION_AUTO_GENERATE` |

## Persistencia

- `cotizaciones.subtotal` guarda el total de la cotizacion.
- `cotizacion_items` guarda una copia de cada linea cotizada.
- Cada linea conserva cantidad, precio unitario y monto total.
- Los precios no se guardan en `items_compra`, porque pueden cambiar entre cotizaciones.
