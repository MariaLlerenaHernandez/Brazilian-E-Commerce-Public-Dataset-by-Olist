-- =====================================================================
-- 01_staging.sql
-- Crea el esquema staging, zona de aterrizaje de los datos YA LIMPIOS por
-- etl/02_limpieza.py (pandas). La carga la realiza etl/03_carga.py con COPY.
-- Tipos correctos desde el origen: fechas TIMESTAMP, códigos postales CHAR(5).
-- =====================================================================
DROP SCHEMA IF EXISTS staging CASCADE;
CREATE SCHEMA staging;

CREATE TABLE staging.orders (
    order_id                      VARCHAR(32) PRIMARY KEY,
    customer_id                   VARCHAR(32) NOT NULL,
    order_status                  VARCHAR(20) NOT NULL,
    order_purchase_timestamp      TIMESTAMP   NOT NULL,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    flag_fechas_incoherentes      SMALLINT    NOT NULL
);

CREATE TABLE staging.order_items (
    order_id      VARCHAR(32)   NOT NULL,
    order_item_id SMALLINT      NOT NULL,
    product_id    VARCHAR(32)   NOT NULL,
    seller_id     VARCHAR(32)   NOT NULL,
    price         NUMERIC(10,2) NOT NULL,
    freight_value NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE staging.order_payments (
    order_id             VARCHAR(32)   NOT NULL,
    payment_sequential   SMALLINT      NOT NULL,
    payment_type         VARCHAR(20)   NOT NULL,
    payment_installments SMALLINT      NOT NULL,
    payment_value        NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE staging.order_reviews (
    review_id            VARCHAR(32) NOT NULL,
    order_id             VARCHAR(32) PRIMARY KEY,   -- una reseña por pedido
    review_score         SMALLINT    NOT NULL,
    review_creation_date TIMESTAMP
);

CREATE TABLE staging.customers (
    customer_id        VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    codigo_postal      CHAR(5),
    ciudad             VARCHAR(100),
    estado             CHAR(2)
);

CREATE TABLE staging.sellers (
    seller_id     VARCHAR(32) PRIMARY KEY,
    codigo_postal CHAR(5),
    ciudad        VARCHAR(100),
    estado        CHAR(2)
);

CREATE TABLE staging.products (
    product_id   VARCHAR(32) PRIMARY KEY,
    categoria_pt VARCHAR(100) NOT NULL,
    peso_g       INTEGER,
    largo_cm     INTEGER,
    alto_cm      INTEGER,
    ancho_cm     INTEGER
);

CREATE TABLE staging.category_translation (
    categoria_pt VARCHAR(100) PRIMARY KEY,
    categoria_en VARCHAR(100) NOT NULL
);

-- Bitácora del ETL: permite comparar filas originales vs. filas cargadas
CREATE TABLE staging.etl_log (
    tabla             VARCHAR(40) PRIMARY KEY,
    filas_origen      INTEGER NOT NULL,
    filas_limpias     INTEGER NOT NULL,
    filas_descartadas INTEGER NOT NULL,
    acciones          TEXT,
    fecha_carga       TIMESTAMP DEFAULT now()
);
