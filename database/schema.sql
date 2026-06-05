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
    unidad VARCHAR,
    cantidad NUMERIC
);

CREATE TABLE IF NOT EXISTS ejecuciones_log (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    estado VARCHAR NOT NULL,
    mensaje TEXT,
    ejecutado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
