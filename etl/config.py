"""
config.py
Configuración común del proceso ETL: rutas del proyecto y parámetros de conexión
a PostgreSQL. Los valores se leen de variables de entorno (archivo .env en la
raíz del proyecto) y, si no existen, se usan los valores del docker-compose.yml.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Carga opcional del archivo .env (python-dotenv). Si no está instalado, se
# siguen usando las variables de entorno del sistema.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:  # pragma: no cover
    pass

RAW_DIR = ROOT / "data" / "raw"        # CSV originales descargados de Kaggle
CLEAN_DIR = ROOT / "data" / "clean"    # CSV limpios generados por 02_limpieza.py
REPORTS_DIR = ROOT / "reports"         # perfilado, bitácora de limpieza y validaciones
SQL_DIR = ROOT / "sql"

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "bi_database"),
    "user": os.getenv("DB_USER", "bi_user"),
    "password": os.getenv("DB_PASSWORD", "bi_pass"),
}

# Archivos del dataset (nombres originales de Kaggle)
ARCHIVOS = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# Período de análisis con datos consistentes (definido en el Entregable 1)
FECHA_INI = "2017-01-01"
FECHA_FIN = "2018-08-31"
