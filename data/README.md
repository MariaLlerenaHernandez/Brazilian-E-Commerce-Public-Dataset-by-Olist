# Datos

Los archivos originales **no se versionan** en el repositorio (≈ 125 MB).

1. Descargar el dataset desde Kaggle:
   <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>
2. Descomprimir los 9 archivos CSV en `data/raw/`:

```
data/raw/
├── olist_customers_dataset.csv
├── olist_geolocation_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── product_category_name_translation.csv
```

`data/clean/` lo genera `etl/02_limpieza.py` y tampoco se versiona.
