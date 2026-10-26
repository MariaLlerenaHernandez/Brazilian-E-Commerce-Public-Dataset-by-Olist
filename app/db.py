"""
db.py
Capa de acceso a datos de la aplicación. TODA la información del dashboard se
obtiene de PostgreSQL (esquema dw) mediante las funciones de sql/06_funciones.sql.
La aplicación no lee ningún CSV.

Parámetros de conexión: variables de entorno (archivo .env en la raíz del
proyecto) con los mismos valores por defecto del docker-compose.yml.
"""
import os
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # pragma: no cover
    pass

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "bi_database"),
    "user": os.getenv("DB_USER", "bi_user"),
    "password": os.getenv("DB_PASSWORD", "bi_pass"),
}

# Funciones SQL que la aplicación puede invocar (lista blanca: evita inyección
# SQL a través del nombre de la función).
FUNCIONES = {
    "fn_kpis",
    "fn_ingresos_mensuales",
    "fn_ventas_por_categoria",
    "fn_ventas_por_estado",
    "fn_csat_por_puntualidad",
    "fn_csat_por_retraso",
    "fn_medios_pago",
    "fn_ranking_vendedores",
}


@st.cache_resource(show_spinner=False)
def _conexion():
    conn = psycopg2.connect(**DB)
    conn.autocommit = True  # solo lectura: cada consulta es independiente
    return conn


def consultar(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Ejecuta una consulta parametrizada y devuelve un DataFrame."""
    try:
        conn = _conexion()
        if conn.closed:
            raise psycopg2.OperationalError("conexión cerrada")
    except psycopg2.OperationalError:
        _conexion.clear()
        conn = _conexion()
    with conn.cursor() as cur:
        cur.execute(sql, params or {})
        columnas = [d[0] for d in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columnas)
    # NUMERIC llega como Decimal: se convierte a número para gráficos y formatos
    for c in df.columns:
        if df[c].dtype == object and len(df) and df[c].map(lambda v: hasattr(v, "as_tuple")).any():
            df[c] = pd.to_numeric(df[c])
    return df


def sql_legible(funcion: str, params: dict) -> str:
    """Texto de la llamada SQL con los valores de los filtros (para mostrarla en la app)."""
    def lit(v):
        return "NULL" if v is None else (str(v) if isinstance(v, (int, float)) else f"'{v}'")

    args = ",\n    ".join(f"{k} => {lit(v)}" for k, v in params.items())
    return f"SELECT *\nFROM dw.{funcion}(\n    {args}\n);"


@st.cache_data(ttl=600, show_spinner="Consultando PostgreSQL…")
def llamar(funcion: str, **params) -> pd.DataFrame:
    """Llama a una función del esquema dw usando notación con nombre:
    SELECT * FROM dw.fn_x(p_fecha_ini => %(p_fecha_ini)s, ...)"""
    if funcion not in FUNCIONES:
        raise ValueError(f"Función no permitida: {funcion}")
    args = ", ".join(f"{k} => %({k})s" for k in params)
    return consultar(f"SELECT * FROM dw.{funcion}({args})", params)


@st.cache_data(ttl=3600, show_spinner=False)
def catalogo(sql: str) -> list:
    """Listas de valores para los filtros, leídas de las dimensiones."""
    return consultar(sql).iloc[:, 0].dropna().tolist()
