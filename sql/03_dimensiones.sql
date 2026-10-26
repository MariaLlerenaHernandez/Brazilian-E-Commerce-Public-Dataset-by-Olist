-- =====================================================================
-- 03_dimensiones.sql
-- Puebla las 6 dimensiones a partir de staging (datos ya limpios).
-- Se puede volver a ejecutar: vacía las tablas antes de cargarlas.
-- =====================================================================
TRUNCATE dw.fact_ventas, dw.dim_tiempo, dw.dim_cliente, dw.dim_producto,
         dw.dim_vendedor, dw.dim_estado_pedido, dw.dim_pago RESTART IDENTITY;

-- ---------- Función auxiliar: región de Brasil a partir del estado (UF) ----------
CREATE OR REPLACE FUNCTION dw.fn_region(p_uf TEXT)
RETURNS TEXT LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN p_uf IN ('AC','AP','AM','PA','RO','RR','TO')                THEN 'Norte'
        WHEN p_uf IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE')      THEN 'Nordeste'
        WHEN p_uf IN ('DF','GO','MT','MS')                               THEN 'Centro-Oeste'
        WHEN p_uf IN ('ES','MG','RJ','SP')                               THEN 'Sudeste'
        WHEN p_uf IN ('PR','RS','SC')                                    THEN 'Sur'
        ELSE 'Sin región'
    END;
$$;

-- ---------- dim_tiempo: calendario completo 2017-2018 (730 días) ----------
INSERT INTO dw.dim_tiempo
SELECT to_char(d, 'YYYYMMDD')::int,
       d::date,
       extract(day FROM d)::smallint,
       extract(isodow FROM d)::smallint,
       (ARRAY['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'])[extract(isodow FROM d)],
       extract(week FROM d)::smallint,
       extract(month FROM d)::smallint,
       (ARRAY['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto',
              'Septiembre','Octubre','Noviembre','Diciembre'])[extract(month FROM d)],
       extract(quarter FROM d)::smallint,
       extract(year FROM d)::smallint,
       extract(isodow FROM d) IN (6, 7)
FROM generate_series('2017-01-01'::date, '2018-12-31'::date, interval '1 day') AS d;

-- ---------- dim_cliente: una fila por customer_id ----------
INSERT INTO dw.dim_cliente (customer_id, customer_unique_id, ciudad, estado, region, codigo_postal)
SELECT customer_id, customer_unique_id, ciudad, estado, dw.fn_region(estado), codigo_postal
FROM staging.customers;

-- ---------- dim_producto: categoría en portugués e inglés, volumen derivado ----------
INSERT INTO dw.dim_producto (product_id, categoria_pt, categoria_en, peso_g, volumen_cm3)
SELECT p.product_id,
       p.categoria_pt,
       COALESCE(t.categoria_en, p.categoria_pt),
       p.peso_g,
       p.largo_cm * p.alto_cm * p.ancho_cm            -- variable derivada
FROM staging.products p
LEFT JOIN staging.category_translation t ON t.categoria_pt = p.categoria_pt;

-- ---------- dim_vendedor ----------
INSERT INTO dw.dim_vendedor (seller_id, ciudad, estado, region)
SELECT seller_id, ciudad, estado, dw.fn_region(estado)
FROM staging.sellers;

-- ---------- dim_estado_pedido: 8 estados con descripción y grupo ----------
INSERT INTO dw.dim_estado_pedido (order_status, descripcion_es, grupo) VALUES
    ('delivered',   'Entregado',               'completado'),
    ('shipped',     'Enviado',                 'en proceso'),
    ('invoiced',    'Facturado',               'en proceso'),
    ('processing',  'En preparación',          'en proceso'),
    ('approved',    'Aprobado',                'en proceso'),
    ('created',     'Creado',                  'en proceso'),
    ('canceled',    'Cancelado',               'fallido'),
    ('unavailable', 'No disponible',           'fallido');

-- ---------- dim_pago: combinación tipo de pago x rango de cuotas (5 x 4 = 20) ----------
INSERT INTO dw.dim_pago (tipo_pago, rango_cuotas)
SELECT t.tipo_pago, r.rango
FROM (SELECT DISTINCT payment_type AS tipo_pago FROM staging.order_payments) t
CROSS JOIN (VALUES ('1'), ('2-6'), ('7-12'), ('>12')) AS r(rango)
ORDER BY t.tipo_pago, r.rango;
