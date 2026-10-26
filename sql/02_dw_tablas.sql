-- =====================================================================
-- 02_dw_tablas.sql
-- Crea el esquema dw con el modelo estrella (solo estructura, sin datos).
-- Granularidad de fact_ventas: una fila por cada ítem de producto vendido
-- dentro de un pedido (order_id + order_item_id).
-- =====================================================================
DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

-- ---------------------------- DIMENSIONES ----------------------------
CREATE TABLE dw.dim_tiempo (
    tiempo_key   INTEGER     PRIMARY KEY,            -- formato AAAAMMDD, p. ej. 20171124
    fecha        DATE        NOT NULL UNIQUE,
    dia          SMALLINT    NOT NULL,
    dia_semana   SMALLINT    NOT NULL,               -- 1 = lunes ... 7 = domingo
    nombre_dia   VARCHAR(12) NOT NULL,
    semana       SMALLINT    NOT NULL,
    mes          SMALLINT    NOT NULL,
    nombre_mes   VARCHAR(12) NOT NULL,
    trimestre    SMALLINT    NOT NULL,
    anio         SMALLINT    NOT NULL,
    es_fin_semana BOOLEAN    NOT NULL
);

CREATE TABLE dw.dim_cliente (
    cliente_key        SERIAL       PRIMARY KEY,
    customer_id        VARCHAR(32)  NOT NULL UNIQUE,
    customer_unique_id VARCHAR(32)  NOT NULL,
    ciudad             VARCHAR(100),
    estado             CHAR(2),
    region             VARCHAR(20),
    codigo_postal      CHAR(5)
);

CREATE TABLE dw.dim_producto (
    producto_key  SERIAL       PRIMARY KEY,
    product_id    VARCHAR(32)  NOT NULL UNIQUE,
    categoria_pt  VARCHAR(100) NOT NULL,
    categoria_en  VARCHAR(100) NOT NULL,
    peso_g        INTEGER,
    volumen_cm3   INTEGER
);

CREATE TABLE dw.dim_vendedor (
    vendedor_key SERIAL       PRIMARY KEY,
    seller_id    VARCHAR(32)  NOT NULL UNIQUE,
    ciudad       VARCHAR(100),
    estado       CHAR(2),
    region       VARCHAR(20)
);

CREATE TABLE dw.dim_estado_pedido (
    estado_key     SERIAL      PRIMARY KEY,
    order_status   VARCHAR(20) NOT NULL UNIQUE,
    descripcion_es VARCHAR(40) NOT NULL,
    grupo          VARCHAR(20) NOT NULL              -- completado / en proceso / fallido
);

CREATE TABLE dw.dim_pago (
    pago_key     SERIAL      PRIMARY KEY,
    tipo_pago    VARCHAR(20) NOT NULL,
    rango_cuotas VARCHAR(10) NOT NULL,               -- 1, 2-6, 7-12, >12
    UNIQUE (tipo_pago, rango_cuotas)
);

-- -------------------------- TABLA DE HECHOS --------------------------
CREATE TABLE dw.fact_ventas (
    order_id      VARCHAR(32)   NOT NULL,            -- dimensión degenerada
    order_item_id SMALLINT      NOT NULL,
    tiempo_key    INTEGER  NOT NULL REFERENCES dw.dim_tiempo(tiempo_key),
    cliente_key   INTEGER  NOT NULL REFERENCES dw.dim_cliente(cliente_key),
    producto_key  INTEGER  NOT NULL REFERENCES dw.dim_producto(producto_key),
    vendedor_key  INTEGER  NOT NULL REFERENCES dw.dim_vendedor(vendedor_key),
    estado_key    INTEGER  NOT NULL REFERENCES dw.dim_estado_pedido(estado_key),
    pago_key      INTEGER  NOT NULL REFERENCES dw.dim_pago(pago_key),
    precio        NUMERIC(10,2) NOT NULL,
    valor_flete   NUMERIC(10,2) NOT NULL,
    valor_total   NUMERIC(10,2) NOT NULL,
    dias_entrega  INTEGER,                           -- NULL si no fue entregado
    dias_retraso  INTEGER,                           -- negativo = adelantado
    flag_a_tiempo SMALLINT,                          -- 1 a tiempo, 0 con retraso
    review_score  SMALLINT,
    PRIMARY KEY (order_id, order_item_id)
);

-- Índices sobre las claves foráneas para acelerar las consultas del dashboard
CREATE INDEX ix_fact_tiempo   ON dw.fact_ventas (tiempo_key);
CREATE INDEX ix_fact_cliente  ON dw.fact_ventas (cliente_key);
CREATE INDEX ix_fact_producto ON dw.fact_ventas (producto_key);
CREATE INDEX ix_fact_vendedor ON dw.fact_ventas (vendedor_key);
CREATE INDEX ix_fact_estado   ON dw.fact_ventas (estado_key);
CREATE INDEX ix_fact_pago     ON dw.fact_ventas (pago_key);
