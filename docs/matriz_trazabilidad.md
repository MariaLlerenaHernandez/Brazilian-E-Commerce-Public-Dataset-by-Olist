# Matriz de trazabilidad · Necesidad de negocio → componente → datos → SQL

Filtros globales (barra lateral, aplican a **todos** los componentes): **F1** rango de fechas ·
**F2** región del cliente · **F3** estado (UF) del cliente · **F4** categoría de producto ·
**F5** medio de pago principal. Todos se envían como parámetros a `dw.fn_ventas_filtradas`,
que es la base común de las demás funciones.

## 1. Matriz principal

| # | Componente (página) | Pregunta / KPI | Filtros | Datos utilizados (modelo) | Vista / Función SQL |
|---|---|---|---|---|---|
| 1 | Tarjeta Ingreso total (Inicio) | P1 · KPI 1 Ingreso total (GMV) | F1–F5 | `fact_ventas.precio` · `dim_tiempo` · `dim_cliente` · `dim_producto` · `dim_pago` · `dim_estado_pedido` | `dw.fn_kpis()` → `ingreso_total` |
| 2 | Tarjeta Ticket promedio (Inicio) | P1 · KPI 2 Ticket promedio | F1–F5 | `fact_ventas.valor_total`, `order_id` (dim. degenerada) | `dw.fn_kpis()` → `ticket_promedio` |
| 3 | Tarjeta Entregas a tiempo (Inicio, Logística) | P2 · KPI 3 % OTD | F1–F5 | `fact_ventas.flag_a_tiempo` (una fila por pedido) | `dw.fn_kpis()` → `pct_a_tiempo` |
| 4 | Tarjeta Satisfacción (Inicio, Logística) | P3 · KPI 4 CSAT | F1–F5 | `fact_ventas.review_score` (una fila por pedido) | `dw.fn_kpis()` → `csat_promedio` |
| 5 | Tarjeta Tiempo de entrega (Inicio, Logística) | P2 · KPI 5 Tiempo promedio de entrega | F1–F5 | `fact_ventas.dias_entrega` | `dw.fn_kpis()` → `dias_entrega_promedio` |
| 6 | Tarjeta Reseñas negativas (Inicio) | P3 · KPI 6 % reseñas negativas | F1–F5 | `fact_ventas.review_score ≤ 2` | `dw.fn_kpis()` → `pct_resenas_negativas` |
| 7 | Tarjetas Pedidos y Flete total (Inicio) | P1 · indicadores de contexto | F1–F5 | `order_id`, `fact_ventas.valor_flete` | `dw.fn_kpis()` → `pedidos`, `total_flete` |
| 8 | Gráfico de líneas Ingresos por mes (Inicio) | P1 · evolución, estacionalidad, variación % | F1–F5 | `fact_ventas.precio` + `dim_tiempo.anio/mes` | `dw.fn_ingresos_mensuales()` |
| 9 | Barras Satisfacción según puntualidad (Inicio) | P3 · CSAT a tiempo vs. con retraso | F1–F5 | `flag_a_tiempo` + `review_score` | `dw.fn_csat_por_puntualidad()` |
| 10 | Barras Ingresos por categoría (Ventas) | P1 · categorías líderes | F1–F5 + Top N | `precio` + `dim_producto.categoria_en` | `dw.fn_ventas_por_categoria()` |
| 11 | Barras Ingresos por estado (Ventas) | P1 · estados líderes y concentración | F1–F5 | `precio` + `dim_cliente.estado/region` | `dw.fn_ventas_por_estado()` |
| 12 | Barras Medios de pago y Ticket por cuotas (Ventas) | P4 · medio de pago y cuotas | F1–F5 | `dim_pago.tipo_pago/rango_cuotas` + `valor_total` | `dw.fn_medios_pago()` |
| 13 | Barras Entregas a tiempo por estado (Logística) | P2 · estados con retrasos | F1–F5 | `flag_a_tiempo`, `dias_entrega` + `dim_cliente.estado` | `dw.fn_ventas_por_estado()` |
| 14 | Barras Satisfacción por días de retraso (Logística) | P3 · intensidad del efecto del retraso | F1–F5 | `dias_retraso` + `review_score` | `dw.fn_csat_por_retraso()` |
| 15 | Tabla Detalle por estado (Logística) | P1/P2 · detalle por estado | F1–F5 | igual que 11 y 13 | `dw.fn_ventas_por_estado()` |
| 16 | Tabla Ranking de vendedores (Vendedores) | P2 · vendedores con retrasos y malas reseñas | F1–F5 + orden, mínimo de pedidos, filas | `precio`, `flag_a_tiempo`, `dias_entrega`, `review_score` + `dim_vendedor` | `dw.fn_ranking_vendedores()` |

## 2. Trazabilidad de los filtros

| Filtro del dashboard | Widget | Parámetro SQL | Columna filtrada (vista base) | Dimensión de origen |
|---|---|---|---|---|
| F1 Rango de fechas | `st.date_input` | `p_fecha_ini`, `p_fecha_fin` | `fecha` | `dim_tiempo.fecha` |
| F2 Región del cliente | `st.selectbox` | `p_region` | `region_cliente` | `dim_cliente.region` |
| F3 Estado (UF) del cliente | `st.selectbox` (en cascada con F2) | `p_estado` | `estado_cliente` | `dim_cliente.estado` |
| F4 Categoría de producto | `st.selectbox` | `p_categoria` | `categoria` | `dim_producto.categoria_en` |
| F5 Medio de pago principal | `st.selectbox` | `p_tipo_pago` | `tipo_pago` | `dim_pago.tipo_pago` |

Un parámetro `NULL` significa “todos”. Las opciones de cada filtro se leen de las dimensiones
(`SELECT DISTINCT … FROM dw.dim_*`), nunca de los CSV.

## 3. Definición de cada KPI

| KPI | Fórmula sobre el modelo | Cuidado de cálculo |
|---|---|---|
| Ingreso total (GMV) | `SUM(precio)` | Excluye pedidos `canceled` y `unavailable` |
| Ticket promedio | `SUM(valor_total) / COUNT(DISTINCT order_id)` | Incluye flete; cuenta pedidos distintos |
| % entregas a tiempo (OTD) | `100 × AVG(flag_a_tiempo)` | Una fila por pedido; solo pedidos `delivered` con fecha |
| Satisfacción (CSAT) | `AVG(review_score)` | Una fila por pedido: la reseña no se repite por ítem |
| Tiempo promedio de entrega | `AVG(dias_entrega)` | Fecha de entrega − fecha de compra, en días |
| % reseñas negativas | `100 × COUNT(review_score ≤ 2) / COUNT(review_score)` | Una fila por pedido |
| % con retraso (vendedor) | `100 × AVG(1 − flag_a_tiempo)` | Una fila por vendedor y pedido |
