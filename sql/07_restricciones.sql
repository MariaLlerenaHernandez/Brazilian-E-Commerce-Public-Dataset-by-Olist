-- =====================================================================
-- 07_restricciones.sql
-- Refuerza el modelo con restricciones CHECK (reglas de calidad en la base).
-- Se puede ejecutar varias veces: primero elimina la restricción si ya existe.
-- Prueba: UPDATE dw.fact_ventas SET review_score = 9 ... debe ser rechazado.
-- =====================================================================

-- ----------------------------- fact_ventas -----------------------------
ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_precio;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_precio CHECK (precio >= 0);

ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_flete;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_flete CHECK (valor_flete >= 0);

ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_total;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_total CHECK (valor_total = precio + valor_flete);

ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_review;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_review
    CHECK (review_score IS NULL OR review_score BETWEEN 1 AND 5);

ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_flag;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_flag
    CHECK (flag_a_tiempo IS NULL OR flag_a_tiempo IN (0, 1));

ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_dias_entrega;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_dias_entrega
    CHECK (dias_entrega IS NULL OR dias_entrega >= 0);

ALTER TABLE dw.fact_ventas DROP CONSTRAINT IF EXISTS ck_fact_item;
ALTER TABLE dw.fact_ventas ADD CONSTRAINT ck_fact_item CHECK (order_item_id > 0);

-- ----------------------------- dimensiones -----------------------------
ALTER TABLE dw.dim_cliente DROP CONSTRAINT IF EXISTS ck_cliente_estado;
ALTER TABLE dw.dim_cliente ADD CONSTRAINT ck_cliente_estado CHECK (estado ~ '^[A-Z]{2}$');

ALTER TABLE dw.dim_cliente DROP CONSTRAINT IF EXISTS ck_cliente_cp;
ALTER TABLE dw.dim_cliente ADD CONSTRAINT ck_cliente_cp CHECK (codigo_postal ~ '^[0-9]{5}$');

ALTER TABLE dw.dim_vendedor DROP CONSTRAINT IF EXISTS ck_vendedor_estado;
ALTER TABLE dw.dim_vendedor ADD CONSTRAINT ck_vendedor_estado CHECK (estado ~ '^[A-Z]{2}$');

ALTER TABLE dw.dim_producto DROP CONSTRAINT IF EXISTS ck_producto_medidas;
ALTER TABLE dw.dim_producto ADD CONSTRAINT ck_producto_medidas
    CHECK ((peso_g IS NULL OR peso_g > 0) AND (volumen_cm3 IS NULL OR volumen_cm3 > 0));

ALTER TABLE dw.dim_tiempo DROP CONSTRAINT IF EXISTS ck_tiempo_calendario;
ALTER TABLE dw.dim_tiempo ADD CONSTRAINT ck_tiempo_calendario
    CHECK (mes BETWEEN 1 AND 12 AND trimestre BETWEEN 1 AND 4 AND dia_semana BETWEEN 1 AND 7);

ALTER TABLE dw.dim_estado_pedido DROP CONSTRAINT IF EXISTS ck_estado_grupo;
ALTER TABLE dw.dim_estado_pedido ADD CONSTRAINT ck_estado_grupo
    CHECK (grupo IN ('completado', 'en proceso', 'fallido'));

ALTER TABLE dw.dim_pago DROP CONSTRAINT IF EXISTS ck_pago_tipo;
ALTER TABLE dw.dim_pago ADD CONSTRAINT ck_pago_tipo
    CHECK (tipo_pago IN ('credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined'));

ALTER TABLE dw.dim_pago DROP CONSTRAINT IF EXISTS ck_pago_cuotas;
ALTER TABLE dw.dim_pago ADD CONSTRAINT ck_pago_cuotas
    CHECK (rango_cuotas IN ('1', '2-6', '7-12', '>12'));
