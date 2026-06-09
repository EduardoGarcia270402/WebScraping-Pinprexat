CREATE TABLE IF NOT EXISTS procesos (
    id SERIAL PRIMARY KEY,
    codigo_necesidad VARCHAR UNIQUE NOT NULL,
    nombre_entidad VARCHAR,
    tipo_necesidad VARCHAR,
    estado_necesidad VARCHAR,
    fecha_publicacion DATE,
    fecha_limite DATE,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_procesos_codigo_necesidad
    ON procesos (codigo_necesidad);

CREATE TABLE IF NOT EXISTS funcionarios (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER UNIQUE NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    nombre VARCHAR,
    correo VARCHAR
);

CREATE TABLE IF NOT EXISTS lugares_entrega (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER UNIQUE NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    provincia VARCHAR,
    canton VARCHAR,
    parroquia VARCHAR,
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS items_compra (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    numero INTEGER,
    cpc VARCHAR,
    categoria_cpc VARCHAR,
    descripcion_producto TEXT,
    unidad VARCHAR,
    cantidad NUMERIC
);

CREATE TABLE IF NOT EXISTS proveedores (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    numero INTEGER,
    ruc_id VARCHAR,
    razon_social TEXT
);

CREATE TABLE IF NOT EXISTS documentos_anexos (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    descripcion_archivo TEXT,
    download_url TEXT,
    nombre_archivo VARCHAR,
    ruta_local TEXT,
    drive_file_id VARCHAR,
    drive_url TEXT
);

CREATE TABLE IF NOT EXISTS especificaciones_pdf (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER UNIQUE NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    documento_anexo_id INTEGER REFERENCES documentos_anexos(id) ON DELETE SET NULL,
    plazo_ejecucion TEXT,
    garantia TEXT,
    validez_proforma TEXT,
    terminos_condiciones TEXT,
    texto_extraido TEXT,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cotizaciones (
    id SERIAL PRIMARY KEY,
    proceso_id INTEGER NOT NULL REFERENCES procesos(id) ON DELETE CASCADE,
    numero_cotizacion VARCHAR UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    ruta_pdf TEXT,
    drive_file_id VARCHAR,
    drive_url TEXT,
    estado VARCHAR NOT NULL DEFAULT 'generada',
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ejecuciones_log (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    estado VARCHAR NOT NULL,
    mensaje TEXT,
    ejecutado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
