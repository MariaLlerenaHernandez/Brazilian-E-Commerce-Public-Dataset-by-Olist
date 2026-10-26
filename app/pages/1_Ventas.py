"""
1_Ventas.py  ·  Página 2: Análisis de ventas
P1: ¿Qué categorías y estados generan más ingresos?
P4 (complementaria): ¿Qué medios de pago y cuántas cuotas prefieren los clientes?
Fuentes: dw.fn_ventas_por_categoria, dw.fn_ventas_por_estado, dw.fn_medios_pago.
"""
import plotly.graph_objects as go
import streamlit as st

from componentes import (AZUL, AZUL_CLARO, NOMBRE_PAGO, configurar_pagina, estilo, filtros_sidebar,
                         moneda, moneda_corta, pct, resumen_filtros, sin_datos, ver_sql)
from db import llamar

configurar_pagina("Ventas", "🛒")
p = filtros_sidebar()

st.title("Ventas por categoría, estado y medio de pago")
st.caption(f"P1 · ¿Qué categorías de productos y estados de Brasil generan más ingresos? · {resumen_filtros(p)}")

# ------------------------------------------------------------ categorías
izq, der = st.columns(2, gap="large")
with izq:
    st.subheader("Ingresos por categoría")
    top = st.slider("Número de categorías", 5, 20, 10, key="top_categorias")
    pc = {**p, "p_limite": top}
    cat = llamar("fn_ventas_por_categoria", **pc)
    if not sin_datos(cat):
        cat = cat.sort_values("ingreso")  # barras horizontales: la mayor arriba
        fig = go.Figure(go.Bar(
            y=cat.categoria, x=cat.ingreso, orientation="h", marker_color=AZUL,
            text=[moneda_corta(v) for v in cat.ingreso], textposition="outside", cliponaxis=False,
            customdata=cat[["pedidos", "participacion_pct", "precio_promedio"]],
            hovertemplate="<b>%{y}</b><br>Ingreso: R$ %{x:,.2f}<br>Pedidos: %{customdata[0]:,}"
                          "<br>Participación: %{customdata[1]:.1f} %<br>Precio promedio: R$ %{customdata[2]:,.2f}"
                          "<extra></extra>",
        ))
        fig.update_xaxes(showticklabels=False)
        fig.update_layout(margin=dict(r=70))
        st.plotly_chart(estilo(fig, alto=max(320, 32 * len(cat))), use_container_width=True)
        ver_sql("fn_ventas_por_categoria", pc)

# ------------------------------------------------------------ estados
with der:
    st.subheader("Ingresos por estado del cliente")
    est = llamar("fn_ventas_por_estado", **p)
    if not sin_datos(est):
        top_est = est.head(12).sort_values("ingreso")
        fig = go.Figure(go.Bar(
            y=top_est.estado, x=top_est.ingreso, orientation="h", marker_color=AZUL,
            text=[f"{moneda_corta(v)} ({pct(s)})" for v, s in zip(top_est.ingreso, top_est.participacion_pct)],
            textposition="outside", cliponaxis=False,
            customdata=top_est[["region", "pedidos"]],
            hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>Ingreso: R$ %{x:,.2f}"
                          "<br>Pedidos: %{customdata[1]:,}<extra></extra>",
        ))
        fig.update_xaxes(showticklabels=False)
        fig.update_layout(margin=dict(r=110))
        st.plotly_chart(estilo(fig, alto=max(320, 32 * len(top_est))), use_container_width=True)
        st.caption("Se muestran los 12 estados con mayor ingreso; la tabla completa está en la página de logística.")
        ver_sql("fn_ventas_por_estado", p)

st.divider()

# ------------------------------------------------------------ medios de pago
st.subheader("Medios de pago y cuotas")
st.caption("P4 (complementaria) · ¿Qué medios de pago y cuántas cuotas prefieren los clientes según el valor del pedido?")
mp = llamar("fn_medios_pago", **p)
if not sin_datos(mp):
    mp["medio"] = mp.tipo_pago.map(NOMBRE_PAGO).fillna(mp.tipo_pago)
    a, b = st.columns(2, gap="large")
    with a:
        por_medio = mp.groupby("medio", as_index=False).pedidos.sum().sort_values("pedidos")
        total = por_medio.pedidos.sum()
        fig = go.Figure(go.Bar(
            y=por_medio.medio, x=por_medio.pedidos, orientation="h", marker_color=AZUL,
            text=[f"{v / total:.1%}".replace(".", ",") for v in por_medio.pedidos],
            textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Pedidos: %{x:,}<extra></extra>",
        ))
        fig.update_xaxes(showticklabels=False)
        fig.update_layout(margin=dict(r=60))
        st.markdown("**Participación en pedidos**")
        st.plotly_chart(estilo(fig, alto=260), use_container_width=True)
    with b:
        tarjeta = mp[mp.tipo_pago == "credit_card"]
        st.markdown("**Ticket promedio según cuotas (tarjeta de crédito)**")
        if tarjeta.empty:
            st.info("El filtro actual no incluye pagos con tarjeta de crédito.")
        else:
            fig = go.Figure(go.Bar(
                x=tarjeta.rango_cuotas, y=tarjeta.ticket_promedio, marker_color=AZUL_CLARO,
                marker_line_color=AZUL, marker_line_width=1,
                text=[moneda(v, 0) for v in tarjeta.ticket_promedio], textposition="outside", cliponaxis=False,
                customdata=tarjeta[["pedidos"]],
                hovertemplate="<b>%{x} cuotas</b><br>Ticket: R$ %{y:,.2f}<br>Pedidos: %{customdata[0]:,}<extra></extra>",
            ))
            fig.update_xaxes(title_text="Rango de cuotas")
            st.plotly_chart(estilo(fig, alto=260, titulo_y="R$ por pedido"), use_container_width=True)
    ver_sql("fn_medios_pago", p)
