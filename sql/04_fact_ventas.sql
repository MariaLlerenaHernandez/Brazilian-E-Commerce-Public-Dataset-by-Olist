-- =====================================================================
-- 04_fact_ventas.sql
-- Carga la tabla de hechos uniendo staging con las dimensiones.
-- Grano: una fila por ítem de pedido (order_id + order_item_id).
-- Alcance: pedidos comprados entre 2017-01-01 y 2018-08-31 (meses completos;
-- los meses de 2016 y sep-oct 2018 están incompletos, ver Entregable 1).
-- =====================================================================
TRUNCATE dw.fact_ventas;

INSERT INTO dw.fact_ventas (
    order_id, order_item_id, tiempo_key, cliente_key, producto_key, vendedor_key,
    estado_key, pago_key, precio, valor_flete, valor_total,
    dias_entrega, dias_retraso, flag_a_tiempo, review_score)
WITH pago_principal AS (
    -- Un pedido puede tener varios pagos (tarjeta + voucher). Se toma como
    -- pago principal el de MAYOR valor; en caso de empate, el primero.
    SELECT DISTINCT ON (order_id)
           order_id,
           payment_type,
           CASE WHEN payment_installments <= 1  THEN '1'
                WHEN payment_installments <= 6  THEN '2-6'
                WHEN payment_installments <= 12 THEN '7-12'
                ELSE '>12' END AS rango_cuotas
    FROM staging.order_payments
    ORDER BY order_id, payment_value DESC, payment_sequential
),
base AS (
    SELECT i.order_id,
           i.order_item_id,
           i.product_id,
           i.seller_id,
           i.price,
           i.freight_value,
           o.customer_id,
           o.order_status,
           o.order_purchase_timestamp::date      AS f_compra,
           -- Las medidas de entrega solo se calculan para pedidos 'delivered'
           -- (un pedido cancelado con fecha de entrega no es una entrega válida).
           CASE WHEN o.order_status = 'delivered'
                THEN o.order_delivered_customer_date::date END AS f_entrega,
           o.order_estimated_delivery_date::date AS f_estimada,
           COALESCE(pp.payment_type, 'not_defined') AS payment_type,
           COALESCE(pp.rango_cuotas, '1')           AS rango_cuotas,
           r.review_score
    FROM staging.order_items i
    JOIN staging.orders o           ON o.order_id = i.order_id
    LEFT JOIN pago_principal pp     ON pp.order_id = i.order_id
    LEFT JOIN staging.order_reviews r ON r.order_id = i.order_id
    WHERE o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-09-01'
)
SELECT b.order_id,
       b.order_item_id,
       to_char(b.f_compra, 'YYYYMMDD')::int,
       c.cliente_key,
       p.producto_key,
       v.vendedor_key,
       e.estado_key,
       pg.pago_key,
       b.price,
       b.freight_value,
       b.price + b.freight_value,                               -- valor_total
       b.f_entrega - b.f_compra,                                -- dias_entrega (NULL si no se entregó)
       b.f_entrega - b.f_estimada,                              -- dias_retraso (negativo = adelantado)
       CASE WHEN b.f_entrega IS NULL THEN NULL
            WHEN b.f_entrega <= b.f_estimada THEN 1 ELSE 0 END, -- flag_a_tiempo
       b.review_score
FROM base b
JOIN dw.dim_cliente c       ON c.customer_id  = b.customer_id
JOIN dw.dim_producto p      ON p.product_id   = b.product_id
JOIN dw.dim_vendedor v      ON v.seller_id    = b.seller_id
JOIN dw.dim_estado_pedido e ON e.order_status = b.order_status
JOIN dw.dim_pago pg         ON pg.tipo_pago   = b.payment_type
                           AND pg.rango_cuotas = b.rango_cuotas;

ANALYZE dw.fact_ventas;
