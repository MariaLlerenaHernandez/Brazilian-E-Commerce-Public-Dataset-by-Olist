"""
2_Logistica_y_Satisfaccion.py  ·  Página 3: Logística y satisfacción
P2: ¿Qué porcentaje de pedidos se entrega a tiempo y en qué estados se concentran los retrasos?
P3: ¿Influyen los retrasos en la satisfacción del cliente?
Fuentes: dw.fn_kpis, dw.fn_ventas_por_estado, dw.fn_csat_por_retraso.
"""
import plotly.graph_objects as go
import streamlit as st

from componentes import (AZUL, AZUL_CLARO, ROJO, configurar_pagina, estilo, filtros_sidebar,
                         numero, pct, resumen_filtros, sin_datos, ver_sql)
from db import llamar

configurar_pagina("Logística y satisfacción", "🚚")
p = filtros_sidebar()

st.title("Logística y satisfacción del cliente")
st.caption(f"P2 y P3 · Puntualidad de las entregas y su efecto en las reseñas · {resumen_filtros(p)}")

k = llamar("fn_kpis", **p)
if k.empty or not k.at[0, "pedidos"]:
    st.info("No hay datos para la combinación de filtros seleccionada. Ajuste o restablezca los filtros.")
    st.stop()
k = k.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Entregas a tiempo (OTD)", pct(k.pct_a_tiempo))
c2.metric("Pedidos con retraso", pct(100 - k.pct_a_tiempo) if k.pct_a_tiempo is not None else "—")
c3.metric("Tiempo promedio de entrega", f"{numero(k.dias_entrega_promedio, 1)} días")
c4.metric("Satisfacción (CSAT)", f"{numero(k.csat_promedio, 2)} / 5")

st.divider()
izq, der = st.columns(2, gap="large")

# ------------------------------------------------------------ P2: OTD por estado
est = llamar("fn_ventas_por_estado", **p)
with izq:
    st.subheader("Entregas a tiempo por estado")
    # Umbral de representatividad: 100 pedidos; si el filtro es muy específico
    # y ningún estado lo alcanza, se muestran todos los estados con entregas.
    umbral = 100 if (not est.empty and est.pedidos.max() >= 100) else 1
    st.caption(f"Estados con al menos {umbral} pedido(s), ordenados de menor a mayor puntualidad. "
               "En rojo, los que están por debajo del promedio del filtro.")
    e = est[(est.pedidos >= umbral) & est.pct_a_tiempo.notna()] if not est.empty else est
    if not sin_datos(e):
        e = e.sort_values("pct_a_tiempo", ascending=False)
        promedio = k.pct_a_tiempo
        colores = [ROJO if promedio is not None and v < promedio else AZUL for v in e.pct_a_tiempo]
        fig = go.Figure(go.Bar(
            y=e.estado, x=e.pct_a_tiempo, orientation="h", marker_color=colores,
            text=[pct(v) for v in e.pct_a_tiempo], textposition="outside", cliponaxis=False,
            customdata=e[["region", "pedidos", "dias_entrega_promedio"]],
            hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>A tiempo: %{x:.1f} %<br>"
                          "Pedidos: %{customdata[1]:,}<br>Días de entrega: %{customdata[2]:.1f}<extra></extra>",
        ))
        if promedio is not None:
            fig.add_vline(x=promedio, line_dash="dot", line_color="#52514e",
                          annotation_text=f"Promedio {pct(promedio)}", annotation_position="top")
        fig.update_xaxes(range=[min(60, e.pct_a_tiempo.min() - 5) if len(e) else 60, 102], showticklabels=False)
        st.plotly_chart(estilo(fig, alto=max(340, 24 * len(e))), use_container_width=True)
        ver_sql("fn_ventas_por_estado", p)

# ------------------------------------------------------------ P3: CSAT por tramo de retraso
with der:
    st.subheader("Satisfacción según días de retraso")
    st.caption("Fecha real de entrega − fecha estimada, agrupada en tramos. Una reseña por pedido.")
    r = llamar("fn_csat_por_retraso", **p)
    if not sin_datos(r):
        colores = [AZUL_CLARO if o <= 3 else ROJO for o in r.orden]
        fig = go.Figure(go.Bar(
            x=r.tramo, y=r.csat_promedio, marker_color=colores,
            text=[numero(v, 2) for v in r.csat_promedio], textposition="outside", cliponaxis=False,
            customdata=r[["pedidos", "pct_resenas_negativas"]],
            hovertemplate="<b>%{x}</b><br>CSAT: %{y:.2f}<br>Pedidos: %{customdata[0]:,}"
                          "<br>Reseñas negativas: %{customdata[1]:.1f} %<extra></extra>",
        ))
        fig.update_yaxes(range=[0, 5.3])
        fig.update_xaxes(tickangle=-30)
        st.plotly_chart(estilo(fig, alto=380, titulo_y="CSAT promedio (1–5)"), use_container_width=True)
        st.markdown(
            f"<span style='color:{AZUL_CLARO}'>■</span> Entregado antes o en la fecha estimada &nbsp; "
            f"<span style='color:{ROJO}'>■</span> Entregado con retraso",
            unsafe_allow_html=True,
        )
        ver_sql("fn_csat_por_retraso", p)

# ------------------------------------------------------------ tabla de detalle por estado
st.divider()
st.subheader("Detalle por estado del cliente")
if not est.empty:
    st.dataframe(
        est.rename(columns={
            "estado": "Estado", "region": "Región", "pedidos": "Pedidos", "ingreso": "Ingreso (R$)",
            "participacion_pct": "% del ingreso", "pct_a_tiempo": "% a tiempo",
            "dias_entrega_promedio": "Días de entrega", "csat_promedio": "CSAT",
        }),
        hide_index=True, use_container_width=True,
        column_config={
            "Ingreso (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            "% del ingreso": st.column_config.NumberColumn(format="%.1f %%"),
            "% a tiempo": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
            "Días de entrega": st.column_config.NumberColumn(format="%.1f"),
            "CSAT": st.column_config.NumberColumn(format="%.2f ★"),
        },
    )
