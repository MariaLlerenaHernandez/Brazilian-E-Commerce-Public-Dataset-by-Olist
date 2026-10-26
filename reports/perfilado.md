# Perfilado del dataset Olist (datos originales)

Total de filas en los 9 archivos: **1,550,922** · columnas: **52**

## orders (olist_orders_dataset.csv)

- Filas: **99,441** · Columnas: **8**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| order_id | object | 0 | 0.0 % | 99,441 |
| customer_id | object | 0 | 0.0 % | 99,441 |
| order_status | object | 0 | 0.0 % | 8 |
| order_purchase_timestamp | object | 0 | 0.0 % | 98,875 |
| order_approved_at | object | 160 | 0.2 % | 90,733 |
| order_delivered_carrier_date | object | 1,783 | 1.8 % | 81,018 |
| order_delivered_customer_date | object | 2,965 | 3.0 % | 95,664 |
| order_estimated_delivery_date | object | 0 | 0.0 % | 459 |

## order_items (olist_order_items_dataset.csv)

- Filas: **112,650** · Columnas: **7**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| order_id | object | 0 | 0.0 % | 98,666 |
| order_item_id | int64 | 0 | 0.0 % | 21 |
| product_id | object | 0 | 0.0 % | 32,951 |
| seller_id | object | 0 | 0.0 % | 3,095 |
| shipping_limit_date | object | 0 | 0.0 % | 93,318 |
| price | float64 | 0 | 0.0 % | 5,968 |
| freight_value | float64 | 0 | 0.0 % | 6,999 |

Estadísticas numéricas:

|       |   order_item_id |     price |   freight_value |
|:------|----------------:|----------:|----------------:|
| count |       112650    | 112650    |       112650    |
| mean  |            1.2  |    120.65 |           19.99 |
| std   |            0.71 |    183.63 |           15.81 |
| min   |            1    |      0.85 |            0    |
| 25%   |            1    |     39.9  |           13.08 |
| 50%   |            1    |     74.99 |           16.26 |
| 75%   |            1    |    134.9  |           21.15 |
| max   |           21    |   6735    |          409.68 |


## order_payments (olist_order_payments_dataset.csv)

- Filas: **103,886** · Columnas: **5**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| order_id | object | 0 | 0.0 % | 99,440 |
| payment_sequential | int64 | 0 | 0.0 % | 29 |
| payment_type | object | 0 | 0.0 % | 5 |
| payment_installments | int64 | 0 | 0.0 % | 24 |
| payment_value | float64 | 0 | 0.0 % | 29,077 |

Estadísticas numéricas:

|       |   payment_sequential |   payment_installments |   payment_value |
|:------|---------------------:|-----------------------:|----------------:|
| count |            103886    |              103886    |       103886    |
| mean  |                 1.09 |                   2.85 |          154.1  |
| std   |                 0.71 |                   2.69 |          217.49 |
| min   |                 1    |                   0    |            0    |
| 25%   |                 1    |                   1    |           56.79 |
| 50%   |                 1    |                   1    |          100    |
| 75%   |                 1    |                   4    |          171.84 |
| max   |                29    |                  24    |        13664.1  |


## order_reviews (olist_order_reviews_dataset.csv)

- Filas: **99,224** · Columnas: **7**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| review_id | object | 0 | 0.0 % | 98,410 |
| order_id | object | 0 | 0.0 % | 98,673 |
| review_score | int64 | 0 | 0.0 % | 5 |
| review_comment_title | object | 87,656 | 88.3 % | 4,527 |
| review_comment_message | object | 58,247 | 58.7 % | 36,159 |
| review_creation_date | object | 0 | 0.0 % | 636 |
| review_answer_timestamp | object | 0 | 0.0 % | 98,248 |

Estadísticas numéricas:

|       |   review_score |
|:------|---------------:|
| count |       99224    |
| mean  |           4.09 |
| std   |           1.35 |
| min   |           1    |
| 25%   |           4    |
| 50%   |           5    |
| 75%   |           5    |
| max   |           5    |


## customers (olist_customers_dataset.csv)

- Filas: **99,441** · Columnas: **5**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| customer_id | object | 0 | 0.0 % | 99,441 |
| customer_unique_id | object | 0 | 0.0 % | 96,096 |
| customer_zip_code_prefix | int64 | 0 | 0.0 % | 14,994 |
| customer_city | object | 0 | 0.0 % | 4,119 |
| customer_state | object | 0 | 0.0 % | 27 |

Estadísticas numéricas:

|       |   customer_zip_code_prefix |
|:------|---------------------------:|
| count |                    99441   |
| mean  |                    35137.5 |
| std   |                    29797.9 |
| min   |                     1003   |
| 25%   |                    11347   |
| 50%   |                    24416   |
| 75%   |                    58900   |
| max   |                    99990   |


## sellers (olist_sellers_dataset.csv)

- Filas: **3,095** · Columnas: **4**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| seller_id | object | 0 | 0.0 % | 3,095 |
| seller_zip_code_prefix | int64 | 0 | 0.0 % | 2,246 |
| seller_city | object | 0 | 0.0 % | 611 |
| seller_state | object | 0 | 0.0 % | 23 |

Estadísticas numéricas:

|       |   seller_zip_code_prefix |
|:------|-------------------------:|
| count |                   3095   |
| mean  |                  32291.1 |
| std   |                  32713.5 |
| min   |                   1001   |
| 25%   |                   7093.5 |
| 50%   |                  14940   |
| 75%   |                  64552.5 |
| max   |                  99730   |


## products (olist_products_dataset.csv)

- Filas: **32,951** · Columnas: **9**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| product_id | object | 0 | 0.0 % | 32,951 |
| product_category_name | object | 610 | 1.9 % | 73 |
| product_name_lenght | float64 | 610 | 1.9 % | 66 |
| product_description_lenght | float64 | 610 | 1.9 % | 2,960 |
| product_photos_qty | float64 | 610 | 1.9 % | 19 |
| product_weight_g | float64 | 2 | 0.0 % | 2,204 |
| product_length_cm | float64 | 2 | 0.0 % | 99 |
| product_height_cm | float64 | 2 | 0.0 % | 102 |
| product_width_cm | float64 | 2 | 0.0 % | 95 |

Estadísticas numéricas:

|       |   product_name_lenght |   product_description_lenght |   product_photos_qty |   product_weight_g |   product_length_cm |   product_height_cm |   product_width_cm |
|:------|----------------------:|-----------------------------:|---------------------:|-------------------:|--------------------:|--------------------:|-------------------:|
| count |              32341    |                     32341    |             32341    |           32949    |            32949    |            32949    |           32949    |
| mean  |                 48.48 |                       771.5  |                 2.19 |            2276.47 |               30.82 |               16.94 |              23.2  |
| std   |                 10.25 |                       635.12 |                 1.74 |            4282.04 |               16.91 |               13.64 |              12.08 |
| min   |                  5    |                         4    |                 1    |               0    |                7    |                2    |               6    |
| 25%   |                 42    |                       339    |                 1    |             300    |               18    |                8    |              15    |
| 50%   |                 51    |                       595    |                 1    |             700    |               25    |               13    |              20    |
| 75%   |                 57    |                       972    |                 3    |            1900    |               38    |               21    |              30    |
| max   |                 76    |                      3992    |                20    |           40425    |              105    |              105    |             118    |


## geolocation (olist_geolocation_dataset.csv)

- Filas: **1,000,163** · Columnas: **5**
- Filas duplicadas (idénticas): **261,831**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| geolocation_zip_code_prefix | int64 | 0 | 0.0 % | 19,015 |
| geolocation_lat | float64 | 0 | 0.0 % | 717,360 |
| geolocation_lng | float64 | 0 | 0.0 % | 717,613 |
| geolocation_city | object | 0 | 0.0 % | 8,011 |
| geolocation_state | object | 0 | 0.0 % | 27 |

Estadísticas numéricas:

|       |   geolocation_zip_code_prefix |   geolocation_lat |   geolocation_lng |
|:------|------------------------------:|------------------:|------------------:|
| count |                   1.00016e+06 |       1.00016e+06 |       1.00016e+06 |
| mean  |               36574.2         |     -21.18        |     -46.39        |
| std   |               30549.3         |       5.72        |       4.27        |
| min   |                1001           |     -36.61        |    -101.47        |
| 25%   |               11075           |     -23.6         |     -48.57        |
| 50%   |               26530           |     -22.92        |     -46.64        |
| 75%   |               63504           |     -19.98        |     -43.77        |
| max   |               99990           |      45.07        |     121.11        |


## category_translation (product_category_name_translation.csv)

- Filas: **71** · Columnas: **2**
- Filas duplicadas (idénticas): **0**

| Columna | Tipo leído | Nulos | % nulos | Valores distintos |
|---|---|---:|---:|---:|
| product_category_name | object | 0 | 0.0 % | 71 |
| product_category_name_english | object | 0 | 0.0 % | 71 |

## Hallazgos de calidad

- Pedidos `delivered` sin fecha de entrega: **8**
- Pedidos entregados a la transportista antes de ser aprobados: **1,359**
- Productos sin categoría: **610** · sin peso o con peso 0: **6**
- Categorías sin traducción: **pc_gamer, portateis_cozinha_e_preparadores_de_alimentos**
- Reseñas: review_id repetidos **814** · pedidos con más de una reseña **547**
- Geolocalización: filas idénticas **261,831** · prefijos postales distintos **19,015**
- Precio: mediana R$ 74.99 · máximo R$ 6,735.00 · ítems sobre el límite IQR (R$ 277.40): **8,427**
- Ítems con flete 0: **383** · pagos con valor 0: **9** · pagos con 0 cuotas: **2**
- payment_type = not_defined: **3**
- Pedidos sin ítems: **775** · pedidos sin pago: **1**

Pedidos por mes (para detectar meses incompletos):

| order_purchase_timestamp   |   pedidos |
|:---------------------------|----------:|
| 2016-09                    |         4 |
| 2016-10                    |       324 |
| 2016-12                    |         1 |
| 2017-01                    |       800 |
| 2017-02                    |      1780 |
| 2017-03                    |      2682 |
| 2017-04                    |      2404 |
| 2017-05                    |      3700 |
| 2017-06                    |      3245 |
| 2017-07                    |      4026 |
| 2017-08                    |      4331 |
| 2017-09                    |      4285 |
| 2017-10                    |      4631 |
| 2017-11                    |      7544 |
| 2017-12                    |      5673 |
| 2018-01                    |      7269 |
| 2018-02                    |      6728 |
| 2018-03                    |      7211 |
| 2018-04                    |      6939 |
| 2018-05                    |      6873 |
| 2018-06                    |      6167 |
| 2018-07                    |      6292 |
| 2018-08                    |      6512 |
| 2018-09                    |        16 |
| 2018-10                    |         4 |
