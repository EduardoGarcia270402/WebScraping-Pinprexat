-- Ver ultimos procesos guardados
SELECT
    id,
    codigo_necesidad,
    nombre_entidad,
    tipo_necesidad,
    estado_necesidad,
    fecha_publicacion,
    fecha_limite,
    creado_en,
    actualizado_en
FROM procesos
ORDER BY id DESC
LIMIT 10;

-- Ver funcionario y lugar de entrega por proceso
SELECT
    p.codigo_necesidad,
    f.nombre AS funcionario_nombre,
    f.correo AS funcionario_correo,
    l.provincia,
    l.canton,
    l.parroquia,
    l.direccion
FROM procesos p
LEFT JOIN funcionarios f ON f.proceso_id = p.id
LEFT JOIN lugares_entrega l ON l.proceso_id = p.id
ORDER BY p.id DESC
LIMIT 10;

-- Ver items de compra guardados
SELECT
    p.codigo_necesidad,
    i.numero,
    i.cpc,
    i.unidad,
    i.cantidad
FROM procesos p
JOIN items_compra i ON i.proceso_id = p.id
ORDER BY p.id DESC, i.numero ASC;

-- Ver ultimas ejecuciones
SELECT
    id,
    url,
    estado,
    mensaje,
    ejecutado_en
FROM ejecuciones_log
ORDER BY id DESC
LIMIT 10;
