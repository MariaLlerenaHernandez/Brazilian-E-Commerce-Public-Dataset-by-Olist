-- =====================================================================
-- 06_funciones.sql
-- Capa de consumo analítico: vista base y funciones que alimentan el
-- dashboard de Streamlit. La aplicación NO lee CSV: solo llama a estas funciones.
--
-- Convención de filtros (igual en todas las funciones):
--   p_fecha_ini, p_fecha_fin  rango de fecha de compra
--   p_region                  región del cliente (Norte, Nordeste, ...)
--   p_categoria               categoría del producto (en inglés)
--   p_estado                  estado (UF) del cliente, p. ej. 'SP'
--   p_tipo_pago               medio de pago principal del pedido
--   Un parámetro NULL significa "todos".
-- Los pedidos cancelados / no disponibles se excluyen de los KPI de venta.
-- =====================================================================

-- Se elimina la vista con CASCADE para poder volver a ejecutar el script
-- aunque cambien sus columnas (también elimina las funciones que dependen de ella).
DROP VIEW IF EXISTS dw.vw_ventas_detalle CASCADE;

-- ---------- Vista base: hechos + todas las dimensiones ----------
CREATE VIEW dw.vw_ventas_detalle AS
SELECT f.order_id,
       f.order_item_id,
       t.fecha,
       t.anio,
       t.mes,
       t.nombre_mes,
       t.trimestre,
       c.customer_unique_id,
       c.ciudad          AS ciudad_cliente,
       c.estado          AS estado_cliente,
       c.region          AS region_cliente,
       p.categoria_pt,
       p.categoria_en    AS categoria,
       v.seller_id,
       v.ciudad          AS ciudad_vendedor,
       v.estado          AS estado_vendedor,
       v.region          AS region_vendedor,
       e.order_status,
       e.descripcion_es  AS estado_pedido,
       e.grupo           AS grupo_estado,
       (e.order_status IN ('canceled', 'unavailable')) AS es_cancelado,
       pg.tipo_pago,
       pg.rango_cuotas,
       f.precio,
       f.valor_flete,
       f.valor_total,
       f.dias_entrega,
       f.dias_retraso,
       f.flag_a_tiempo,
       f.review_score
FROM dw.fact_ventas f
JOIN dw.dim_tiempo        t  ON t.tiempo_key   = f.tiempo_key
JOIN dw.dim_cliente       c  ON c.cliente_key  = f.cliente_key
JOIN dw.dim_producto      p  ON p.producto_key = f.producto_key
JOIN dw.dim_vendedor      v  ON v.vendedor_key = f.vendedor_key
JOIN dw.dim_estado_pedido e  ON e.estado_key   = f.estado_key
JOIN dw.dim_pago          pg ON pg.pago_key    = f.pago_key;

-- ---------- Filtro común: una sola definición de los filtros del dashboard ----------
CREATE FUNCTION dw.fn_ventas_filtradas(
    p_fecha_ini DATE DEFAULT '2017-01-01',
    p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region    TEXT DEFAULT NULL,
    p_categoria TEXT DEFAULT NULL,
    p_estado    TEXT DEFAULT NULL,
    p_tipo_pago TEXT DEFAULT NULL)
RETURNS SETOF dw.vw_ventas_detalle
LANGUAGE sql STABLE AS $$
    SELECT *
    FROM dw.vw_ventas_detalle v
    WHERE NOT v.es_cancelado
      AND v.fecha BETWEEN COALESCE(p_fecha_ini, '1900-01-01') AND COALESCE(p_fecha_fin, '2999-12-31')
      AND (p_region    IS NULL OR v.region_cliente = p_region)
      AND (p_categoria IS NULL OR v.categoria      = p_categoria)
      AND (p_estado    IS NULL OR v.estado_cliente = p_estado)
      AND (p_tipo_pago IS NULL OR v.tipo_pago      = p_tipo_pago);
$$;

-- ---------- KPI: tarjetas del dashboard (una sola fila) ----------
CREATE FUNCTION dw.fn_kpis(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL)
RETURNS TABLE (ingreso_total NUMERIC, ticket_promedio NUMERIC, pct_a_tiempo NUMERIC,
               csat_promedio NUMERIC, pedidos BIGINT, dias_entrega_promedio NUMERIC,
               pct_resenas_negativas NUMERIC, total_flete NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH f AS (
        SELECT * FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago)
    ),
    ped AS (  -- una fila por pedido: evita contar dos veces los pedidos con varios ítems
        SELECT DISTINCT ON (order_id) order_id, flag_a_tiempo, review_score, dias_entrega
        FROM f ORDER BY order_id
    )
    SELECT (SELECT round(COALESCE(sum(precio), 0), 2) FROM f),
           (SELECT round(sum(valor_total) / NULLIF(count(DISTINCT order_id), 0), 2) FROM f),
           (SELECT round(100 * avg(flag_a_tiempo), 1) FROM ped),
           (SELECT round(avg(review_score), 2) FROM ped),
           (SELECT count(*) FROM ped),
           (SELECT round(avg(dias_entrega), 1) FROM ped),
           (SELECT round(100.0 * count(*) FILTER (WHERE review_score <= 2)
                         / NULLIF(count(review_score), 0), 1) FROM ped),
           (SELECT round(COALESCE(sum(valor_flete), 0), 2) FROM f);
$$;

-- ---------- P1. Gráfico de líneas: ingresos por mes y variación % ----------
CREATE FUNCTION dw.fn_ingresos_mensuales(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL)
RETURNS TABLE (anio SMALLINT, mes SMALLINT, periodo TEXT, ingreso NUMERIC,
               pedidos BIGINT, ticket_promedio NUMERIC, variacion_pct NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH m AS (
        SELECT v.anio, v.mes,
               sum(v.precio)               AS ingreso,
               sum(v.valor_total)          AS total,
               count(DISTINCT v.order_id)  AS pedidos
        FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago) v
        GROUP BY v.anio, v.mes
    )
    SELECT m.anio::smallint,
           m.mes::smallint,
           (m.anio || '-' || lpad(m.mes::text, 2, '0'))::text,
           round(m.ingreso, 2),
           m.pedidos,
           round(m.total / NULLIF(m.pedidos, 0), 2),
           round(100 * (m.ingreso - lag(m.ingreso) OVER w) / NULLIF(lag(m.ingreso) OVER w, 0), 1)
    FROM m
    WINDOW w AS (ORDER BY m.anio, m.mes)
    ORDER BY m.anio, m.mes;
$$;

-- ---------- P1. Gráfico de barras: ingresos por categoría ----------
CREATE FUNCTION dw.fn_ventas_por_categoria(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL,
    p_limite INTEGER DEFAULT 10)
RETURNS TABLE (categoria TEXT, pedidos BIGINT, items BIGINT, ingreso NUMERIC,
               participacion_pct NUMERIC, precio_promedio NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH c AS (
        SELECT v.categoria,
               count(DISTINCT v.order_id) AS pedidos,
               count(*)                   AS items,
               sum(v.precio)              AS ingreso
        FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago) v
        GROUP BY v.categoria
    )
    SELECT c.categoria::text, c.pedidos, c.items, round(c.ingreso, 2),
           round(100 * c.ingreso / NULLIF(sum(c.ingreso) OVER (), 0), 1),
           round(c.ingreso / NULLIF(c.items, 0), 2)
    FROM c
    ORDER BY c.ingreso DESC
    LIMIT p_limite;
$$;

-- ---------- P1/P2. Desempeño por estado del cliente (ventas + logística) ----------
CREATE FUNCTION dw.fn_ventas_por_estado(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL)
RETURNS TABLE (estado TEXT, region TEXT, pedidos BIGINT, ingreso NUMERIC,
               participacion_pct NUMERIC, pct_a_tiempo NUMERIC,
               dias_entrega_promedio NUMERIC, csat_promedio NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH f AS (
        SELECT * FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago)
    ),
    ing AS (
        SELECT estado_cliente, max(region_cliente) AS region, sum(precio) AS ingreso
        FROM f GROUP BY estado_cliente
    ),
    ped AS (
        SELECT DISTINCT ON (order_id) order_id, estado_cliente, flag_a_tiempo, dias_entrega, review_score
        FROM f ORDER BY order_id
    ),
    met AS (
        SELECT estado_cliente,
               count(*)                         AS pedidos,
               round(100 * avg(flag_a_tiempo), 1) AS pct_a_tiempo,
               round(avg(dias_entrega), 1)      AS dias_entrega,
               round(avg(review_score), 2)      AS csat
        FROM ped GROUP BY estado_cliente
    )
    SELECT ing.estado_cliente::text, ing.region::text, met.pedidos, round(ing.ingreso, 2),
           round(100 * ing.ingreso / NULLIF(sum(ing.ingreso) OVER (), 0), 1),
           met.pct_a_tiempo, met.dias_entrega, met.csat
    FROM ing JOIN met USING (estado_cliente)
    ORDER BY ing.ingreso DESC;
$$;

-- ---------- P3. Gráfico de barras: satisfacción según puntualidad ----------
CREATE FUNCTION dw.fn_csat_por_puntualidad(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL)
RETURNS TABLE (grupo TEXT, pedidos BIGINT, csat_promedio NUMERIC, pct_resenas_negativas NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH ped AS (
        SELECT DISTINCT ON (order_id) order_id, flag_a_tiempo, review_score
        FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago)
        WHERE flag_a_tiempo IS NOT NULL
          AND review_score IS NOT NULL
        ORDER BY order_id
    )
    SELECT (CASE WHEN flag_a_tiempo = 1 THEN 'A tiempo' ELSE 'Con retraso' END)::text,
           count(*),
           round(avg(review_score), 2),
           round(100.0 * count(*) FILTER (WHERE review_score <= 2) / count(*), 1)
    FROM ped
    GROUP BY flag_a_tiempo
    ORDER BY flag_a_tiempo DESC;
$$;

-- ---------- P3. Satisfacción por tramos de días de retraso ----------
CREATE FUNCTION dw.fn_csat_por_retraso(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL)
RETURNS TABLE (orden INTEGER, tramo TEXT, pedidos BIGINT, csat_promedio NUMERIC,
               pct_resenas_negativas NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH ped AS (
        SELECT DISTINCT ON (order_id) order_id, dias_retraso, review_score
        FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago)
        WHERE dias_retraso IS NOT NULL AND review_score IS NOT NULL
        ORDER BY order_id
    ),
    t AS (
        SELECT CASE WHEN dias_retraso <= -15 THEN 1
                    WHEN dias_retraso <= -8  THEN 2
                    WHEN dias_retraso <= 0   THEN 3
                    WHEN dias_retraso <= 3   THEN 4
                    WHEN dias_retraso <= 7   THEN 5
                    WHEN dias_retraso <= 14  THEN 6
                    ELSE 7 END AS orden,
               review_score
        FROM ped
    )
    SELECT t.orden,
           (ARRAY['15+ días antes', '8-14 días antes', '0-7 días antes',
                  '1-3 días tarde', '4-7 días tarde', '8-14 días tarde', '15+ días tarde'])[t.orden],
           count(*),
           round(avg(review_score), 2),
           round(100.0 * count(*) FILTER (WHERE review_score <= 2) / count(*), 1)
    FROM t
    GROUP BY t.orden
    ORDER BY t.orden;
$$;

-- ---------- P4 (complementaria). Medios de pago y cuotas ----------
CREATE FUNCTION dw.fn_medios_pago(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL)
RETURNS TABLE (tipo_pago TEXT, rango_cuotas TEXT, pedidos BIGINT, ingreso NUMERIC,
               ticket_promedio NUMERIC)
LANGUAGE sql STABLE AS $$
    SELECT v.tipo_pago::text,
           v.rango_cuotas::text,
           count(DISTINCT v.order_id),
           round(sum(v.precio), 2),
           round(sum(v.valor_total) / NULLIF(count(DISTINCT v.order_id), 0), 2)
    FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago) v
    GROUP BY v.tipo_pago, v.rango_cuotas
    ORDER BY v.tipo_pago, array_position(ARRAY['1','2-6','7-12','>12'], v.rango_cuotas::text);
$$;

-- ---------- P2. Tabla de detalle: ranking de vendedores ----------
-- p_orden: 'ingreso' (mayor ingreso primero) o 'retraso' (mayor % de retrasos primero)
-- p_min_pedidos: excluye vendedores con muy pocos pedidos (porcentajes poco fiables)
CREATE FUNCTION dw.fn_ranking_vendedores(
    p_fecha_ini DATE DEFAULT '2017-01-01', p_fecha_fin DATE DEFAULT '2018-08-31',
    p_region TEXT DEFAULT NULL, p_categoria TEXT DEFAULT NULL,
    p_estado TEXT DEFAULT NULL, p_tipo_pago TEXT DEFAULT NULL,
    p_limite INTEGER DEFAULT 20,
    p_orden TEXT DEFAULT 'ingreso',
    p_min_pedidos INTEGER DEFAULT 1)
RETURNS TABLE (seller_id TEXT, ciudad TEXT, estado TEXT, pedidos BIGINT, ingreso NUMERIC,
               pct_con_retraso NUMERIC, dias_entrega_promedio NUMERIC, csat_promedio NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH f AS (
        SELECT * FROM dw.fn_ventas_filtradas(p_fecha_ini, p_fecha_fin, p_region, p_categoria, p_estado, p_tipo_pago)
    ),
    ing AS (
        SELECT f.seller_id, max(f.ciudad_vendedor) AS ciudad, max(f.estado_vendedor) AS estado,
               sum(f.precio) AS ingreso
        FROM f GROUP BY f.seller_id
    ),
    ped AS (  -- una fila por vendedor y pedido
        SELECT DISTINCT ON (f.seller_id, f.order_id)
               f.seller_id, f.order_id, f.flag_a_tiempo, f.dias_entrega, f.review_score
        FROM f ORDER BY f.seller_id, f.order_id
    ),
    met AS (
        SELECT ped.seller_id,
               count(*)                                    AS pedidos,
               round(100 * avg(1 - ped.flag_a_tiempo), 1)  AS pct_con_retraso,
               round(avg(ped.dias_entrega), 1)             AS dias_entrega,
               round(avg(ped.review_score), 2)             AS csat_promedio
        FROM ped GROUP BY ped.seller_id
    )
    SELECT ing.seller_id::text, ing.ciudad::text, ing.estado::text, met.pedidos,
           round(ing.ingreso, 2), met.pct_con_retraso, met.dias_entrega, met.csat_promedio
    FROM ing JOIN met USING (seller_id)
    WHERE met.pedidos >= p_min_pedidos
    ORDER BY CASE WHEN p_orden = 'retraso' THEN met.pct_con_retraso END DESC NULLS LAST,
             ing.ingreso DESC
    LIMIT p_limite;
$$;
