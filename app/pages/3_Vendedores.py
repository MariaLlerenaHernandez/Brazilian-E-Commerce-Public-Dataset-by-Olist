"""
3_Vendedores.py  ·  Página 4: Ranking de vendedores (tabla de detalle)
P2: ¿En qué vendedores se concentran los retrasos?
Fuente: dw.fn_ranking_vendedores.
"""
import streamlit as st

from componentes import configurar_pagina, filtros_sidebar, moneda, numero, pct, resumen_filtros, sin_datos, ver_sql
from db import llamar

configurar_pagina("Vendedores", "🏪")
p = filtros_sidebar()

st.title("Ranking de vendedores")
st.caption(f"P2 · ¿En qué vendedores se concentran los retrasos y las malas reseñas? · {resumen_filtros(p)}")

a, b, c = st.columns([2, 1, 1])
orden = a.radio(
    "Ordenar por",
    ["ingreso", "retraso"],
    format_func=lambda v: "Mayor ingreso" if v == "ingreso" else "Mayor % de pedidos con retraso",
    horizontal=True, key="v_orden",
)
minimo = b.number_input("Pedidos mínimos", 1, 1000, 30 if orden == "retraso" else 1, step=10, key=f"v_minimo_{orden}",
                        help="Excluye vendedores con pocos pedidos: sus porcentajes no son representativos.")
limite = c.number_input("Filas", 5, 200, 20, step=5, key="v_limite")

pr = {**p, "p_limite": int(limite), "p_orden": orden, "p_min_pedidos": int(minimo)}
v = llamar("fn_ranking_vendedores", **pr)

if not sin_datos(v):
    m1, m2, m3 = st.columns(3)
    m1.metric("Vendedores listados", numero(len(v)))
    m2.metric("Ingreso de los listados", moneda(v.ingreso.sum()))
    m3.metric("% con retraso (mediana)", pct(v.pct_con_retraso.median()))

    tabla = v.copy()
    tabla.insert(0, "#", range(1, len(tabla) + 1))
    tabla["seller_id"] = tabla.seller_id.str[:8] + "…"
    st.dataframe(
        tabla.rename(columns={
            "seller_id": "Vendedor", "ciudad": "Ciudad", "estado": "UF", "pedidos": "Pedidos",
            "ingreso": "Ingreso (R$)", "pct_con_retraso": "% con retraso",
            "dias_entrega_promedio": "Días de entrega", "csat_promedio": "CSAT",
        }),
        hide_index=True, use_container_width=True, height=min(38 * (len(tabla) + 1), 740),
        column_config={
            "Ingreso (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            "% con retraso": st.column_config.ProgressColumn(format="%.1f %%", min_value=0,
                                                             max_value=max(25.0, float(v.pct_con_retraso.max() or 0))),
            "Días de entrega": st.column_config.NumberColumn(format="%.1f"),
            "CSAT": st.column_config.NumberColumn(format="%.2f ★"),
        },
    )
    st.download_button("Descargar CSV", v.to_csv(index=False).encode("utf-8"),
                       file_name="ranking_vendedores.csv", mime="text/csv")
    ver_sql("fn_ranking_vendedores", pr)

    st.info(
        "Uso sugerido: ordenar por **% con retraso** con un mínimo de 30 pedidos para identificar a los "
        "vendedores a capacitar o advertir; ordenar por **ingreso** para identificar a los vendedores clave "
        "cuyo retraso tiene mayor impacto en el negocio."
    )
