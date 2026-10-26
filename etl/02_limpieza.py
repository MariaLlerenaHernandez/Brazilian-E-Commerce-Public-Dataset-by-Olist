"""
02_limpieza.py
Paso 2 del ETL: limpieza y transformación con pandas.

Lee los CSV originales de data/raw/, aplica los tratamientos definidos en el
Entregable 1 y escribe un CSV limpio por tabla en data/clean/. Además genera
reports/bitacora_limpieza.csv (filas de origen, filas limpias, descartadas y
acciones aplicadas), que luego se carga en staging.etl_log para validar la
coherencia entre los datos originales y los datos cargados.

Uso:  python etl/02_limpieza.py
"""
import unicodedata

import numpy as np
import pandas as pd

from config import ARCHIVOS, CLEAN_DIR, RAW_DIR, REPORTS_DIR

bitacora: list[dict] = []


def registrar(tabla: str, origen: int, limpias: int, acciones: str) -> None:
    bitacora.append(
        {
            "tabla": tabla,
            "filas_origen": origen,
            "filas_limpias": limpias,
            "filas_descartadas": origen - limpias,
            "acciones": acciones,
        }
    )
    print(f"  {tabla:<22} {origen:>9,} -> {limpias:>9,}  | {acciones}")


def leer(nombre: str, **kw) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / ARCHIVOS[nombre], low_memory=False, **kw)


def guardar(df: pd.DataFrame, nombre: str) -> None:
    df.to_csv(CLEAN_DIR / f"{nombre}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Funciones de estandarización
# ---------------------------------------------------------------------------
def sin_tildes(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(ch)
    )


def normalizar_ciudad(serie: pd.Series) -> pd.Series:
    """'São Paulo - SP', 'sao paulo / sao paulo', ' SAO  PAULO ' -> 'sao paulo'."""
    s = serie.fillna("").astype(str).str.lower().str.replace("´", "'").str.replace("`", "'")
    s = s.map(sin_tildes)
    s = s.str.split(r"\s+-\s+|/|\\|,", n=1, regex=True).str[0]  # quita sufijos de estado
    s = s.str.replace(r"[^a-z' ]", " ", regex=True)              # deja solo letras
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()
    s = s.str.replace(r"(?<=\w) (ac|al|ap|am|ba|ce|df|es|go|ma|mt|ms|mg|pa|pb|pr|pe|pi|rj|rn|rs|ro|rr|sc|sp|se|to)$",
                      "", regex=True)                               # 'sao paulo sp' -> 'sao paulo'
    return s.replace("", np.nan)


def zip5(serie: pd.Series) -> pd.Series:
    """Código postal como texto de 5 dígitos (recupera ceros a la izquierda)."""
    return serie.astype("Int64").astype(str).str.zfill(5)


UFS = {
    "ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa",
    "pb", "pr", "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to",
}
CIUDAD_POR_CP: pd.Series = pd.Series(dtype=str)  # se completa en preparar_geolocation()


def corregir_ciudad(original: pd.Series, normalizada: pd.Series, cp: pd.Series) -> tuple[pd.Series, int]:
    """Ciudades inválidas (números, correos, solo la sigla del estado o vacías) se
    imputan con la ciudad más frecuente de su prefijo postal en geolocation."""
    o = original.fillna("").astype(str)
    invalida = (
        o.str.contains(r"\d|@", regex=True)
        | normalizada.isna()
        | normalizada.isin(UFS)
    )
    imputada = cp.map(CIUDAD_POR_CP)
    resultado = normalizada.mask(invalida & imputada.notna(), imputada)
    return resultado, int(invalida.sum())


# ---------------------------------------------------------------------------
# Limpieza por tabla
# ---------------------------------------------------------------------------
FECHAS_ORDERS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def limpiar_orders() -> None:
    df = leer("orders")
    n = len(df)
    df = df.drop_duplicates("order_id")
    for c in FECHAS_ORDERS:  # texto -> datetime
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["order_status"] = df["order_status"].str.strip().str.lower()
    # Bandera de fechas incoherentes (no se borran: son pedidos reales, pero se
    # excluyen del análisis logístico cuando corresponda).
    df["flag_fechas_incoherentes"] = (
        (df.order_delivered_carrier_date < df.order_approved_at)
        | (df.order_delivered_customer_date < df.order_purchase_timestamp)
    ).astype(int)
    guardar(df[["order_id", "customer_id", "order_status", *FECHAS_ORDERS, "flag_fechas_incoherentes"]], "orders")
    registrar(
        "orders", n, len(df),
        "8 fechas texto->datetime; estado en minúsculas; bandera de fechas incoherentes "
        f"({int(df.flag_fechas_incoherentes.sum()):,} pedidos marcados, no eliminados)",
    )


def limpiar_items() -> None:
    df = leer("order_items")
    n = len(df)
    df = df.drop_duplicates(["order_id", "order_item_id"])
    df["price"] = df["price"].round(2)
    df["freight_value"] = df["freight_value"].round(2)
    df = df[(df.price >= 0) & (df.freight_value >= 0)]
    guardar(df[["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"]], "order_items")
    registrar(
        "order_items", n, len(df),
        "sin duplicados por (order_id, order_item_id); se elimina shipping_limit_date; "
        "precios altos y fletes en 0 se conservan (ventas reales)",
    )


def limpiar_payments() -> None:
    df = leer("order_payments")
    n = len(df)
    df = df.drop_duplicates(["order_id", "payment_sequential"])
    df["payment_type"] = df["payment_type"].str.strip().str.lower()
    # 0 cuotas no es posible: se interpreta como pago en una sola cuota
    df.loc[df.payment_installments < 1, "payment_installments"] = 1
    guardar(df[["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"]], "order_payments")
    registrar("order_payments", n, len(df), "cuotas 0 -> 1; 'not_defined' se conserva como categoría válida")


def limpiar_reviews() -> None:
    df = leer("order_reviews", parse_dates=["review_creation_date", "review_answer_timestamp"])
    n = len(df)
    # Una reseña por pedido: se conserva la más reciente
    df = df.sort_values(["order_id", "review_creation_date", "review_answer_timestamp"])
    df = df.drop_duplicates("order_id", keep="last")
    df = df[df.review_score.between(1, 5)]
    guardar(df[["review_id", "order_id", "review_score", "review_creation_date"]], "order_reviews")
    registrar(
        "order_reviews", n, len(df),
        "se conserva la reseña más reciente por pedido; se eliminan título y comentario (texto libre)",
    )


def limpiar_customers() -> None:
    df = leer("customers")
    n = len(df)
    df = df.drop_duplicates("customer_id")
    df["codigo_postal"] = zip5(df.customer_zip_code_prefix)
    df["ciudad"], invalidas = corregir_ciudad(df.customer_city, normalizar_ciudad(df.customer_city), df.codigo_postal)
    df["estado"] = df.customer_state.str.strip().str.upper()
    guardar(df[["customer_id", "customer_unique_id", "codigo_postal", "ciudad", "estado"]], "customers")
    registrar(
        "customers", n, len(df),
        f"código postal a texto de 5 dígitos; ciudad normalizada ({df.ciudad.nunique():,} ciudades); "
        f"{invalidas} ciudades inválidas imputadas por código postal",
    )


def limpiar_sellers() -> None:
    df = leer("sellers")
    n = len(df)
    df = df.drop_duplicates("seller_id")
    df["codigo_postal"] = zip5(df.seller_zip_code_prefix)
    antes = df.seller_city.nunique()
    df["ciudad"], invalidas = corregir_ciudad(df.seller_city, normalizar_ciudad(df.seller_city), df.codigo_postal)
    df["estado"] = df.seller_state.str.strip().str.upper()
    guardar(df[["seller_id", "codigo_postal", "ciudad", "estado"]], "sellers")
    registrar(
        "sellers", n, len(df),
        f"ciudad normalizada ({antes} -> {df.ciudad.nunique()} valores distintos); "
        f"{invalidas} ciudades inválidas (números, correo, solo sigla) imputadas por código postal",
    )


TRADUCCIONES_FALTANTES = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_food_processors",
    "sin_categoria": "no_category",
}


def limpiar_products() -> None:
    df = leer("products")
    n = len(df)
    df = df.drop_duplicates("product_id")
    df = df.rename(
        columns={  # corrige nombres mal escritos y unifica idioma
            "product_category_name": "categoria_pt",
            "product_weight_g": "peso_g",
            "product_length_cm": "largo_cm",
            "product_height_cm": "alto_cm",
            "product_width_cm": "ancho_cm",
        }
    )
    df["categoria_pt"] = df["categoria_pt"].fillna("sin_categoria")
    for c in ["peso_g", "largo_cm", "alto_cm", "ancho_cm"]:
        df[c] = df[c].astype("Int64")         # decimales -> enteros
    df.loc[df.peso_g == 0, "peso_g"] = pd.NA  # peso 0 g no es físicamente posible
    guardar(df[["product_id", "categoria_pt", "peso_g", "largo_cm", "alto_cm", "ancho_cm"]], "products")
    registrar(
        "products", n, len(df),
        "categoría nula -> 'sin_categoria'; medidas a entero; peso 0 -> nulo; "
        "se eliminan name_lenght, description_lenght y photos_qty",
    )


def limpiar_traduccion() -> None:
    df = leer("category_translation")
    n = len(df)
    df.columns = ["categoria_pt", "categoria_en"]
    extra = pd.DataFrame(list(TRADUCCIONES_FALTANTES.items()), columns=df.columns)
    df = pd.concat([df, extra]).drop_duplicates("categoria_pt")
    guardar(df, "category_translation")
    registrar("category_translation", n, len(df), "se completan 2 traducciones faltantes y 'sin_categoria'")


def preparar_geolocation() -> None:
    """Deduplica geolocation y obtiene la ciudad más frecuente por prefijo postal.
    Se usa solo para imputar ciudades inválidas; la tabla no se carga al modelo."""
    global CIUDAD_POR_CP
    df = leer("geolocation")
    n = len(df)
    duplicadas = int(df.duplicated().sum())
    df = df.drop_duplicates()
    df["cp"] = zip5(df.geolocation_zip_code_prefix)
    df["ciudad"] = normalizar_ciudad(df.geolocation_city)
    CIUDAD_POR_CP = df.dropna(subset=["ciudad"]).groupby("cp")["ciudad"].agg(lambda s: s.value_counts().index[0])
    registrar(
        "geolocation", n, 0,
        f"{duplicadas:,} filas idénticas eliminadas; resumida a {len(CIUDAD_POR_CP):,} prefijos postales "
        "para imputar ciudades inválidas; no se carga al modelo (no interviene en los KPI)",
    )


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    print("Limpieza de datos (filas origen -> filas limpias)")
    preparar_geolocation()  # primero: provee la ciudad por código postal
    limpiar_orders()
    limpiar_items()
    limpiar_payments()
    limpiar_reviews()
    limpiar_customers()
    limpiar_sellers()
    limpiar_products()
    limpiar_traduccion()
    pd.DataFrame(bitacora).to_csv(REPORTS_DIR / "bitacora_limpieza.csv", index=False)
    print(f"CSV limpios en {CLEAN_DIR} · bitácora en {REPORTS_DIR / 'bitacora_limpieza.csv'}")


if __name__ == "__main__":
    main()
