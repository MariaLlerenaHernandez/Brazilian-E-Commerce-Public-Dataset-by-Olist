"""
01_perfilado.py
Paso 1 del ETL: análisis y perfilamiento de los 9 CSV originales.

Genera reports/perfilado.md con, para cada tabla: filas, columnas, nulos por
columna, filas duplicadas y estadísticas de las variables numéricas. También
calcula los hallazgos puntuales de calidad documentados en el Entregable 1.

Uso:  python etl/01_perfilado.py
"""
import pandas as pd

from config import ARCHIVOS, RAW_DIR, REPORTS_DIR


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / ARCHIVOS[nombre], low_memory=False)


def perfil_tabla(nombre: str, df: pd.DataFrame) -> list[str]:
    lineas = [f"## {nombre} ({ARCHIVOS[nombre]})", ""]
    lineas.append(f"- Filas: **{len(df):,}** · Columnas: **{df.shape[1]}**")
    lineas.append(f"- Filas duplicadas (idénticas): **{df.duplicated().sum():,}**")
    lineas.append("")
    lineas.append("| Columna | Tipo leído | Nulos | % nulos | Valores distintos |")
    lineas.append("|---|---|---:|---:|---:|")
    for c in df.columns:
        n = df[c].isna().sum()
        lineas.append(
            f"| {c} | {df[c].dtype} | {n:,} | {100 * n / len(df):.1f} % | {df[c].nunique():,} |"
        )
    num = df.select_dtypes("number")
    if not num.empty:
        lineas += ["", "Estadísticas numéricas:", "", num.describe().round(2).to_markdown(), ""]
    lineas.append("")
    return lineas


def hallazgos(t: dict[str, pd.DataFrame]) -> list[str]:
    """Hallazgos de calidad específicos (los mismos del Entregable 1)."""
    o = t["orders"].copy()
    for c in [c for c in o.columns if c.startswith("order_") and c not in ("order_id", "order_status")]:
        o[c] = pd.to_datetime(o[c], errors="coerce")
    i, p, r, pr = t["order_items"], t["order_payments"], t["order_reviews"], t["products"]
    g, tr = t["geolocation"], t["category_translation"]

    q1 = i.price.quantile(0.25)
    q3 = i.price.quantile(0.75)
    lim = q3 + 1.5 * (q3 - q1)
    sin_trad = sorted(set(pr.product_category_name.dropna()) - set(tr.product_category_name))
    mes = o.order_purchase_timestamp.dt.to_period("M").value_counts().sort_index()

    h = [
        "## Hallazgos de calidad",
        "",
        f"- Pedidos `delivered` sin fecha de entrega: **{((o.order_status == 'delivered') & o.order_delivered_customer_date.isna()).sum()}**",
        f"- Pedidos entregados a la transportista antes de ser aprobados: **{(o.order_delivered_carrier_date < o.order_approved_at).sum():,}**",
        f"- Productos sin categoría: **{pr.product_category_name.isna().sum()}** · sin peso o con peso 0: **{(pr.product_weight_g.isna() | (pr.product_weight_g == 0)).sum()}**",
        f"- Categorías sin traducción: **{', '.join(sin_trad)}**",
        f"- Reseñas: review_id repetidos **{r.review_id.duplicated().sum()}** · pedidos con más de una reseña **{r.order_id.value_counts().gt(1).sum()}**",
        f"- Geolocalización: filas idénticas **{g.duplicated().sum():,}** · prefijos postales distintos **{g.geolocation_zip_code_prefix.nunique():,}**",
        f"- Precio: mediana R$ {i.price.median():.2f} · máximo R$ {i.price.max():,.2f} · ítems sobre el límite IQR (R$ {lim:.2f}): **{(i.price > lim).sum():,}**",
        f"- Ítems con flete 0: **{(i.freight_value == 0).sum()}** · pagos con valor 0: **{(p.payment_value == 0).sum()}** · pagos con 0 cuotas: **{(p.payment_installments == 0).sum()}**",
        f"- payment_type = not_defined: **{(p.payment_type == 'not_defined').sum()}**",
        f"- Pedidos sin ítems: **{(~o.order_id.isin(i.order_id)).sum()}** · pedidos sin pago: **{(~o.order_id.isin(p.order_id)).sum()}**",
        "",
        "Pedidos por mes (para detectar meses incompletos):",
        "",
        mes.rename("pedidos").to_frame().to_markdown(),
        "",
    ]
    return h


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    tablas = {n: leer(n) for n in ARCHIVOS}
    total = sum(len(df) for df in tablas.values())
    salida = [
        "# Perfilado del dataset Olist (datos originales)",
        "",
        f"Total de filas en los 9 archivos: **{total:,}** · columnas: **{sum(df.shape[1] for df in tablas.values())}**",
        "",
    ]
    for n, df in tablas.items():
        salida += perfil_tabla(n, df)
    salida += hallazgos(tablas)
    (REPORTS_DIR / "perfilado.md").write_text("\n".join(salida), encoding="utf-8")
    print(f"Perfilado generado en {REPORTS_DIR / 'perfilado.md'}")
    for n, df in tablas.items():
        print(f"  {n:<22} {len(df):>9,} filas  {df.shape[1]:>2} columnas")


if __name__ == "__main__":
    main()
