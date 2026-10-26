-- =====================================================================
-- 05_validaciones.sql
-- Consultas de validación de la carga. Cada consulta debe devolver el
-- resultado esperado indicado en el comentario.
-- Ejecutar: psql -U bi_user -d bi_database -f sql/05_validaciones.sql
-- =====================================================================

-- 0. Coherencia CSV original -> limpieza -> staging
--    Esperado: filas_limpias = filas_en_staging en todas las tablas cargadas.
SELECT '0. Origen vs staging' AS validacion, l.tabla, l.filas_origen, l.filas_limpias,
       l.filas_descartadas, s.filas AS filas_en_staging,
       CASE WHEN l.filas_limpias = COALESCE(s.filas, 0) THEN 'OK' ELSE 'REVISAR' END AS estado
FROM staging.etl_log l
LEFT JOIN (
    SELECT 'orders' AS tabla, count(*) AS filas FROM staging.orders UNION ALL
    SELECT 'order_items', count(*) FROM staging.order_items UNION ALL
    SELECT 'order_payments', count(*) FROM staging.order_payments UNION ALL
    SELECT 'order_reviews', count(*) FROM staging.order_reviews UNION ALL
    SELECT 'customers', count(*) FROM staging.customers UNION ALL
    SELECT 'sellers', count(*) FROM staging.sellers UNION ALL
    SELECT 'products', count(*) FROM staging.products UNION ALL
    SELECT 'category_translation', count(*) FROM staging.category_translation
) s USING (tabla)
ORDER BY l.filas_origen DESC;

-- 1. Cantidad de registros por tabla del modelo
--    Esperado: dim_tiempo 730, dim_estado_pedido 8, dim_pago 20,
--              dim_vendedor 3 095, dim_producto 32 951, dim_cliente 99 441.
SELECT '1. Registros' AS validacion, tabla, filas FROM (
    SELECT 'dim_tiempo' AS tabla, count(*) AS filas FROM dw.dim_tiempo UNION ALL
    SELECT 'dim_cliente', count(*) FROM dw.dim_cliente UNION ALL
    SELECT 'dim_producto', count(*) FROM dw.dim_producto UNION ALL
    SELECT 'dim_vendedor', count(*) FROM dw.dim_vendedor UNION ALL
    SELECT 'dim_estado_pedido', count(*) FROM dw.dim_estado_pedido UNION ALL
    SELECT 'dim_pago', count(*) FROM dw.dim_pago UNION ALL
    SELECT 'fact_ventas', count(*) FROM dw.fact_ventas
) x ORDER BY filas;

-- 1b. Ítems en staging dentro del período vs filas de la tabla de hechos
--     Esperado: ambos valores iguales (112 279). Ninguna fila se pierde en los JOIN.
SELECT '1b. Staging vs fact' AS validacion,
       (SELECT count(*) FROM staging.order_items i JOIN staging.orders o USING (order_id)
         WHERE o.order_purchase_timestamp >= '2017-01-01'
           AND o.order_purchase_timestamp <  '2018-09-01') AS items_staging,
       (SELECT count(*) FROM dw.fact_ventas) AS filas_fact;

-- 2. Integridad referencial: filas de hechos sin dimensión (huérfanas)
--    Esperado: 0 en todas las columnas.
SELECT '2. Huerfanos' AS validacion,
       count(*) FILTER (WHERE t.tiempo_key   IS NULL) AS sin_tiempo,
       count(*) FILTER (WHERE c.cliente_key  IS NULL) AS sin_cliente,
       count(*) FILTER (WHERE p.producto_key IS NULL) AS sin_producto,
       count(*) FILTER (WHERE v.vendedor_key IS NULL) AS sin_vendedor,
       count(*) FILTER (WHERE e.estado_key   IS NULL) AS sin_estado,
       count(*) FILTER (WHERE g.pago_key     IS NULL) AS sin_pago
FROM dw.fact_ventas f
LEFT JOIN dw.dim_tiempo t        ON t.tiempo_key   = f.tiempo_key
LEFT JOIN dw.dim_cliente c       ON c.cliente_key  = f.cliente_key
LEFT JOIN dw.dim_producto p      ON p.producto_key = f.producto_key
LEFT JOIN dw.dim_vendedor v      ON v.vendedor_key = f.vendedor_key
LEFT JOIN dw.dim_estado_pedido e ON e.estado_key   = f.estado_key
LEFT JOIN dw.dim_pago g          ON g.pago_key     = f.pago_key;

-- 2b. Duplicados en el grano de la tabla de hechos. Esperado: 0.
SELECT '2b. Duplicados en fact' AS validacion, count(*) AS duplicados
FROM (SELECT order_id, order_item_id FROM dw.fact_ventas
      GROUP BY 1, 2 HAVING count(*) > 1) d;

-- 2c. Pedidos del período sin ítems (no pueden estar en fact_ventas por su grano)
--     Esperado: 739 pedidos, todos cancelados / no disponibles / creados.
SELECT '2c. Pedidos sin items' AS validacion, count(*) AS pedidos,
       string_agg(DISTINCT o.order_status, ', ') AS estados
FROM staging.orders o
WHERE o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
  AND NOT EXISTS (SELECT 1 FROM staging.order_items i WHERE i.order_id = o.order_id);

-- 3. Valores nulos relevantes en la tabla de hechos
--    Esperado: precio y flete sin nulos. Los nulos de entrega corresponden a
--    pedidos no entregados; los de review_score a pedidos sin reseña.
SELECT '3. Nulos en fact' AS validacion,
       count(*) FILTER (WHERE dias_entrega  IS NULL) AS dias_entrega_nulo,
       count(*) FILTER (WHERE dias_retraso  IS NULL) AS dias_retraso_nulo,
       count(*) FILTER (WHERE flag_a_tiempo IS NULL) AS flag_a_tiempo_nulo,
       count(*) FILTER (WHERE review_score  IS NULL) AS review_nulo,
       count(*) FILTER (WHERE precio IS NULL OR valor_flete IS NULL) AS precio_o_flete_nulo
FROM dw.fact_ventas;

-- 3a. Los nulos de entrega se explican por el estado del pedido
SELECT '3a. Entrega nula por estado' AS validacion, e.order_status, count(*) AS items
FROM dw.fact_ventas f JOIN dw.dim_estado_pedido e USING (estado_key)
WHERE f.dias_entrega IS NULL
GROUP BY e.order_status ORDER BY items DESC;

-- 3b. Nulos en dimensiones
SELECT '3b. Nulos en dimensiones' AS validacion,
       (SELECT count(*) FROM dw.dim_producto WHERE categoria_pt = 'sin_categoria') AS productos_sin_categoria,
       (SELECT count(*) FROM dw.dim_producto WHERE peso_g IS NULL)                 AS productos_sin_peso,
       (SELECT count(*) FROM dw.dim_cliente  WHERE ciudad IS NULL)                 AS clientes_sin_ciudad,
       (SELECT count(*) FROM dw.dim_vendedor WHERE ciudad IS NULL)                 AS vendedores_sin_ciudad;

-- 4. Totales principales (todos los pedidos del período, incluidos cancelados)
SELECT '4. Totales' AS validacion,
       count(*)                                   AS items,
       count(DISTINCT order_id)                   AS pedidos,
       sum(precio)                                AS ingreso_productos,
       sum(valor_flete)                           AS total_flete,
       sum(valor_total)                           AS ingreso_con_flete,
       round(sum(valor_total) / count(DISTINCT order_id), 2) AS ticket_promedio
FROM dw.fact_ventas;

-- 4a. Coherencia de totales: staging (origen limpio) vs tabla de hechos
--     Esperado: diferencia 0,00 en ingreso y flete.
SELECT '4a. Totales staging vs fact' AS validacion,
       s.ingreso AS ingreso_staging, f.ingreso AS ingreso_fact, s.ingreso - f.ingreso AS dif_ingreso,
       s.flete   AS flete_staging,   f.flete   AS flete_fact,   s.flete - f.flete     AS dif_flete
FROM (SELECT sum(i.price) AS ingreso, sum(i.freight_value) AS flete
      FROM staging.order_items i JOIN staging.orders o USING (order_id)
      WHERE o.order_purchase_timestamp >= '2017-01-01'
        AND o.order_purchase_timestamp <  '2018-09-01') s,
     (SELECT sum(precio) AS ingreso, sum(valor_flete) AS flete FROM dw.fact_ventas) f;

-- 4b. valor_total debe ser exactamente precio + flete. Esperado: 0.
SELECT '4b. valor_total inconsistente' AS validacion, count(*) AS filas
FROM dw.fact_ventas WHERE valor_total <> precio + valor_flete;

-- 4c. KPI de entrega y satisfacción calculados directamente sobre la tabla de hechos
SELECT '4c. KPI de entrega y satisfaccion' AS validacion,
       round(avg(dias_entrega), 1)       AS dias_entrega_promedio,
       round(100 * avg(flag_a_tiempo), 1) AS pct_a_tiempo,
       round(avg(review_score), 2)       AS csat_promedio
FROM (SELECT DISTINCT ON (f.order_id) f.dias_entrega, f.flag_a_tiempo, f.review_score
      FROM dw.fact_ventas f JOIN dw.dim_estado_pedido e USING (estado_key)
      WHERE e.order_status NOT IN ('canceled', 'unavailable')
      ORDER BY f.order_id) p;

-- 5. Coherencia de las funciones del dashboard con la tabla de hechos
--    Esperado: la suma de ingresos mensuales = ingreso_total de fn_kpis().
SELECT '5. fn_kpis vs fn_ingresos_mensuales' AS validacion,
       (SELECT ingreso_total FROM dw.fn_kpis())                  AS ingreso_kpi,
       (SELECT sum(ingreso)  FROM dw.fn_ingresos_mensuales())    AS suma_mensual,
       (SELECT sum(ingreso)  FROM dw.fn_ventas_por_estado())     AS suma_estados;
