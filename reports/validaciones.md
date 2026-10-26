# Resultados de las consultas de validación

## 0. Origen vs staging

| tabla | filas_origen | filas_limpias | filas_descartadas | filas_en_staging | estado |
|---|---|---|---|---|---|
| geolocation | 1000163 | 0 | 1000163 |  | OK |
| order_items | 112650 | 112650 | 0 | 112650 | OK |
| order_payments | 103886 | 103886 | 0 | 103886 | OK |
| customers | 99441 | 99441 | 0 | 99441 | OK |
| orders | 99441 | 99441 | 0 | 99441 | OK |
| order_reviews | 99224 | 98673 | 551 | 98673 | OK |
| products | 32951 | 32951 | 0 | 32951 | OK |
| sellers | 3095 | 3095 | 0 | 3095 | OK |
| category_translation | 71 | 74 | -3 | 74 | OK |

## 1. Registros

| tabla | filas |
|---|---|
| dim_estado_pedido | 8 |
| dim_pago | 20 |
| dim_tiempo | 730 |
| dim_vendedor | 3095 |
| dim_producto | 32951 |
| dim_cliente | 99441 |
| fact_ventas | 112279 |

## 1b. Staging vs fact

| items_staging | filas_fact |
|---|---|
| 112279 | 112279 |

## 2. Huerfanos

| sin_tiempo | sin_cliente | sin_producto | sin_vendedor | sin_estado | sin_pago |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 |

## 2b. Duplicados en fact

| duplicados |
|---|
| 0 |

## 2c. Pedidos sin items

| pedidos | estados |
|---|---|
| 739 | canceled, created, unavailable |

## 3. Nulos en fact

| dias_entrega_nulo | dias_retraso_nulo | flag_a_tiempo_nulo | review_nulo | precio_o_flete_nulo |
|---|---|---|---|---|
| 2407 | 2407 | 2407 | 936 | 0 |

## 3a. Entrega nula por estado

| order_status | items |
|---|---|
| shipped | 1174 |
| canceled | 527 |
| processing | 355 |
| invoiced | 340 |
| delivered | 8 |
| approved | 3 |

## 3b. Nulos en dimensiones

| productos_sin_categoria | productos_sin_peso | clientes_sin_ciudad | vendedores_sin_ciudad |
|---|---|---|---|
| 610 | 6 | 0 | 0 |

## 4. Totales

| items | pedidos | ingreso_productos | total_flete | ingreso_con_flete | ticket_promedio |
|---|---|---|---|---|---|
| 112279 | 98353 | 13541712.78 | 2244490.79 | 15786203.57 | 160.51 |

## 4a. Totales staging vs fact

| ingreso_staging | ingreso_fact | dif_ingreso | flete_staging | flete_fact | dif_flete |
|---|---|---|---|---|---|
| 13541712.78 | 13541712.78 | 0.00 | 2244490.79 | 2244490.79 | 0.00 |

## 4b. valor_total inconsistente

| filas |
|---|
| 0 |

## 4c. KPI de entrega y satisfaccion

| dias_entrega_promedio | pct_a_tiempo | csat_promedio |
|---|---|---|
| 12.5 | 93.2 | 4.12 |

## 5. fn_kpis vs fn_ingresos_mensuales

| ingreso_kpi | suma_mensual | suma_estados |
|---|---|---|
| 13449529.68 | 13449529.68 | 13449529.68 |
