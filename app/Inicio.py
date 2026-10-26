"""
Inicio.py  ·  Página 1: Resumen ejecutivo
Ejecutar:  streamlit run app/Inicio.py

KPI principales, evolución mensual de ingresos (P1) y satisfacción según
puntualidad (P3). Fuentes: dw.fn_kpis, dw.fn_ingresos_mensuales,
dw.fn_csat_por_puntualidad.
"""
import plotly.graph_objects as go
import streamlit as st

from componentes import (AZUL, ROJO, VERDE, configurar_pagina, estilo, filtros_sidebar, moneda,
                         moneda_corta, numero, pct, resumen_filtros, sin_datos, ver_sql)
from db import llamar

configurar_pagina("Resumen ejecutivo", "📊")
p = filtros_sidebar()

st.title("Olist E-commerce · Ventas, entregas y satisfacción")
st.caption(f"Data Mart PostgreSQL (esquema `dw`) · {resumen_filtros(p)}")

# ------------------------------------------------------------------ KPI
k = llamar("fn_kpis", **p)
if k.empty or not k.at[0, "pedidos"]:
    st.info("No hay datos para la combinación de filtros seleccionada. Ajuste o restablezca los filtros.")
    st.stop()
k = k.iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingreso total (GMV)", moneda_corta(k.ingreso_total), help="Σ precio de los ítems de pedidos no cancelados")
c2.metric("Ticket promedio", moneda(k.ticket_promedio), help="Σ (precio + flete) / nº de pedidos distintos")
c3.metric("Entregas a tiempo (OTD)", pct(k.pct_a_tiempo), help="Pedidos entregados con fecha real ≤ fecha estimada")
c4.metric("Satisfacción (CSAT)", f"{numero(k.csat_promedio, 2)} / 5", help="Promedio de review_score, una reseña por pedido")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Pedidos", numero(k.pedidos))
c6.metric("Tiempo promedio de entrega", f"{numero(k.dias_entrega_promedio, 1)} días")
c7.metric("Reseñas negativas (1–2 ★)", pct(k.pct_resenas_negativas))
c8.metric("Flete total", moneda_corta(k.total_flete))
ver_sql("fn_kpis", p)

st.divider()

# ------------------------------------------------------------------ gráficos
izq, der = st.columns([3, 2], gap="large")

with izq:
    st.subheader("Ingresos por mes")
    st.caption("P1 · ¿Cómo evolucionan las ventas en el tiempo?")
    m = llamar("fn_ingresos_mensuales", **p)
    if not sin_datos(m):
        fig = go.Figure(go.Scatter(
            x=m.periodo, y=m.ingreso, mode="lines+markers",
            line=dict(color=AZUL, width=2), marker=dict(size=8, color=AZUL),
            customdata=m[["pedidos", "variacion_pct"]],
            hovertemplate="<b>%{x}</b><br>Ingreso: R$ %{y:,.2f}<br>Pedidos: %{customdata[0]:,}"
                          "<br>Variación: %{customdata[1]:+.1f} %<extra></extra>",
        ))
        pico = m.loc[m.ingreso.idxmax()]
        fig.add_annotation(x=pico.periodo, y=pico.ingreso, text=f"Pico {pico.periodo}<br>{moneda_corta(pico.ingreso)}",
                           showarrow=True, arrowhead=0, ay=-36, font=dict(size=12))
        st.plotly_chart(estilo(fig, titulo_y="R$"), use_container_width=True)
        ver_sql("fn_ingresos_mensuales", p)

with der:
    st.subheader("Satisfacción según puntualidad")
    st.caption("P3 · ¿Influyen los retrasos en la satisfacción?")
    c = llamar("fn_csat_por_puntualidad", **p)
    if not sin_datos(c):
        colores = [VERDE if g == "A tiempo" else ROJO for g in c.grupo]
        fig = go.Figure(go.Bar(
            x=c.grupo, y=c.csat_promedio, marker_color=colores, width=0.5,
            text=[f"{numero(v, 2)} ★" for v in c.csat_promedio], textposition="outside",
            customdata=c[["pedidos", "pct_resenas_negativas"]],
            hovertemplate="<b>%{x}</b><br>CSAT: %{y:.2f}<br>Pedidos: %{customdata[0]:,}"
                          "<br>Reseñas negativas: %{customdata[1]:.1f} %<extra></extra>",
        ))
        fig.update_yaxes(range=[0, 5.5])
        st.plotly_chart(estilo(fig, titulo_y="Puntuación promedio (1–5)"), use_container_width=True)
        if len(c) == 2:
            brecha = c.csat_promedio.iloc[0] - c.csat_promedio.iloc[1]
            st.markdown(
                f"Los pedidos con retraso obtienen **{numero(brecha, 2)} puntos menos** de satisfacción; "
                f"sus reseñas negativas suben de **{pct(c.pct_resenas_negativas.iloc[0])}** a "
                f"**{pct(c.pct_resenas_negativas.iloc[1])}**."
            )
        ver_sql("fn_csat_por_puntualidad", p)
