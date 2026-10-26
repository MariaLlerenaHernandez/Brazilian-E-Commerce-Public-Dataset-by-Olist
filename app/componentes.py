"""
componentes.py
Elementos compartidos por todas las páginas:
  - barra lateral con los 5 filtros interactivos (se conservan al cambiar de página)
  - tarjetas KPI, formato de moneda/porcentajes y estilo común de los gráficos
  - expansor "Ver consulta SQL" para mostrar de dónde sale cada resultado
"""
from datetime import date

import plotly.graph_objects as go
import streamlit as st

from db import catalogo, sql_legible

FECHA_MIN = date(2017, 1, 1)
FECHA_MAX = date(2018, 8, 31)
TODAS = "Todas"

# Paleta (validada para daltonismo): serie principal azul; estado bueno / crítico
AZUL = "#2a78d6"
AZUL_CLARO = "#86b6ef"
VERDE = "#0ca30c"
ROJO = "#d03b3b"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRILLA = "#e1e0d9"

DEFAULTS = {
    "f_fechas": (FECHA_MIN, FECHA_MAX),
    "f_region": TODAS,
    "f_estado": TODAS,
    "f_categoria": TODAS,
    "f_pago": TODAS,
}

NOMBRE_PAGO = {
    "credit_card": "Tarjeta de crédito",
    "boleto": "Boleto bancario",
    "voucher": "Voucher",
    "debit_card": "Tarjeta de débito",
    "not_defined": "No definido",
}


# ------------------------------------------------------------------ página
def configurar_pagina(titulo: str, icono: str) -> None:
    st.set_page_config(page_title=f"{titulo} · Olist BI", page_icon=icono, layout="wide")
    st.markdown(
        """
        <style>
          .block-container {padding-top: 2rem;}
          div[data-testid="stMetric"] {
              background: #fcfcfb; border: 1px solid rgba(11,11,11,0.10);
              border-radius: 8px; padding: 12px 16px;}
          div[data-testid="stMetricLabel"] p {color: #52514e; font-size: 0.85rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ filtros
def _persistir(clave: str) -> None:
    """Copia el valor del widget a un almacén que sobrevive al cambio de página."""
    st.session_state["_filtros"][clave] = st.session_state[clave]


def _restablecer() -> None:
    st.session_state["_filtros"] = dict(DEFAULTS)
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def filtros_sidebar() -> dict:
    """Dibuja los filtros y devuelve los parámetros para las funciones SQL.
    Convención: None = "todos" (igual que en sql/06_funciones.sql)."""
    almacen = st.session_state.setdefault("_filtros", dict(DEFAULTS))
    for k, v in almacen.items():  # restaura los valores al entrar a otra página
        st.session_state[k] = v

    sb = st.sidebar
    sb.header("Filtros")
    sb.date_input(
        "Rango de fechas de compra",
        min_value=FECHA_MIN, max_value=FECHA_MAX,
        key="f_fechas", on_change=_persistir, args=("f_fechas",),
        format="DD/MM/YYYY",
    )

    regiones = catalogo("SELECT DISTINCT region FROM dw.dim_cliente ORDER BY 1")
    sb.selectbox("Región del cliente", [TODAS] + regiones,
                 key="f_region", on_change=_persistir, args=("f_region",))

    # El filtro de estado depende de la región seleccionada (filtro en cascada)
    if st.session_state.f_region == TODAS:
        estados = catalogo("SELECT DISTINCT estado FROM dw.dim_cliente ORDER BY 1")
    else:
        region = st.session_state.f_region.replace("'", "''")
        estados = catalogo(f"SELECT DISTINCT estado FROM dw.dim_cliente WHERE region = '{region}' ORDER BY 1")
    if st.session_state.f_estado not in [TODAS] + estados:
        st.session_state.f_estado = TODAS
        almacen["f_estado"] = TODAS
    sb.selectbox("Estado (UF) del cliente", [TODAS] + estados,
                 key="f_estado", on_change=_persistir, args=("f_estado",))

    categorias = catalogo("SELECT DISTINCT categoria_en FROM dw.dim_producto ORDER BY 1")
    sb.selectbox("Categoría de producto", [TODAS] + categorias,
                 key="f_categoria", on_change=_persistir, args=("f_categoria",))

    pagos = catalogo("SELECT DISTINCT tipo_pago FROM dw.dim_pago ORDER BY 1")
    sb.selectbox("Medio de pago principal", [TODAS] + pagos,
                 key="f_pago", on_change=_persistir, args=("f_pago",),
                 format_func=lambda v: NOMBRE_PAGO.get(v, v))

    sb.button("Restablecer filtros", on_click=_restablecer, use_container_width=True)
    sb.caption("Los filtros se envían como parámetros a las funciones SQL del esquema `dw`.")

    fechas = st.session_state.f_fechas
    ini, fin = (fechas if isinstance(fechas, (tuple, list)) and len(fechas) == 2
                else (FECHA_MIN, FECHA_MAX))  # mientras el usuario elige la 2.ª fecha

    def valor(clave):
        v = st.session_state[clave]
        return None if v == TODAS else v

    return {
        "p_fecha_ini": ini,
        "p_fecha_fin": fin,
        "p_region": valor("f_region"),
        "p_categoria": valor("f_categoria"),
        "p_estado": valor("f_estado"),
        "p_tipo_pago": valor("f_pago"),
    }


def resumen_filtros(p: dict) -> str:
    partes = [f"{p['p_fecha_ini']:%d/%m/%Y} – {p['p_fecha_fin']:%d/%m/%Y}"]
    for clave, etiqueta in [("p_region", "Región"), ("p_estado", "UF"),
                            ("p_categoria", "Categoría"), ("p_tipo_pago", "Pago")]:
        if p[clave]:
            partes.append(f"{etiqueta}: {NOMBRE_PAGO.get(p[clave], p[clave])}")
    return " · ".join(partes)


# ------------------------------------------------------------------ formatos
def moneda(v, decimales: int = 2) -> str:
    """Formato brasileño: R$ 13.449.529,68"""
    if v is None:
        return "—"
    texto = f"{v:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def moneda_corta(v) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1e6:
        return f"R$ {v / 1e6:,.2f} M".replace(".", ",")
    if abs(v) >= 1e3:
        return f"R$ {v / 1e3:,.1f} mil".replace(".", ",")
    return moneda(v)


def numero(v, decimales: int = 0) -> str:
    if v is None:
        return "—"
    return f"{v:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, decimales: int = 1) -> str:
    return "—" if v is None else f"{numero(v, decimales)} %"


# ------------------------------------------------------------------ gráficos
def estilo(fig: go.Figure, alto: int = 360, titulo_y: str | None = None) -> go.Figure:
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=8, t=16, b=8),
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=TINTA_2, size=13),
        hoverlabel=dict(bgcolor="white", font=dict(color=TINTA)),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, linecolor="#c3c2b7", tickfont_color="#898781")
    fig.update_yaxes(gridcolor=GRILLA, zeroline=False, tickfont_color="#898781", title_text=titulo_y)
    return fig


def ver_sql(funcion: str, params: dict) -> None:
    with st.expander("Ver consulta SQL"):
        st.code(sql_legible(funcion, params), language="sql")


def sin_datos(df) -> bool:
    if df.empty:
        st.info("No hay datos para la combinación de filtros seleccionada.")
        return True
    return False
