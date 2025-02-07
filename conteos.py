import pyarrow
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
    }

COLORES = ["#ff595e", "#ffca3a", "#8ac926", "#1982c4"]
COLORES_RESP = {
    "N0":"#ff595e",
    "N1":"#ffca3a",
    "N2":"#8ac926",
    "N3":"#1982c4"
    }

diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop(["fase", "nivel", "grado"], axis=1)

conteo_grado = pd.read_parquet("data/item_conteo_grado.parquet")
conteo_grado = conteo_grado.merge(diccionario, how="inner", on="item")
conteo_grado["resp"] = (
    conteo_grado["resp"]
    .astype("category")
    .cat
    .reorder_categories(["N0", "N1", "N2", "N3"], ordered=True)
)

conteo_servicio = pd.read_parquet("data/item_conteo_servicio.parquet")
conteo_servicio = conteo_servicio.merge(diccionario, how="inner", on="item")

procesos = conteo_grado["proceso"].unique()

#### Streamlit ####

st.set_page_config(
    page_title="Conteos - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

st.title("Conteos Evaluación Diagnóstica 2024")

tab_grado, tab_servicios = st.tabs(["Grado", "Servicios"])

with tab_grado:
    with st.sidebar:
        sel_cnt_nivel = st.selectbox("Nivel", options = NIVELES_GRADO.keys(), index=2)
        sel_cnt_grado = st.selectbox("Grado", options = NIVELES_GRADO[sel_cnt_nivel])

    conteo_grado_filtro = conteo_grado.loc[
        (conteo_grado["nivel"] == sel_cnt_nivel) &
        (conteo_grado["grado"] == sel_cnt_grado)
    ].sort_values(["proceso", "consigna", "inciso", "criterio_num"])

    eia_filtro = conteo_grado_filtro["eia"].unique()

    with st.sidebar:
        sel_cnt_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
        sel_cnt_proceso = st.multiselect("Proceso", options = procesos, default=procesos)

    conteo_grado_filtro = conteo_grado_filtro.loc[
        (conteo_grado_filtro["eia"].isin(sel_cnt_eia)) &
        (conteo_grado_filtro["proceso"].isin(sel_cnt_proceso))
    ]

    for eia in conteo_grado_filtro["eia"].unique():
        st.markdown(f"### {eia}")
        conteo_eia = conteo_grado_filtro.loc[conteo_grado_filtro["eia"] == eia]
        fig = px.bar(
            conteo_eia,
            x="item",
            y="prop",
            color="resp",
            text=conteo_eia["prop"].round(),
            color_discrete_sequence=COLORES,
            hover_name="proceso",
            hover_data=["eia", "descriptor", "criterio", "campo"],
            labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"},
            height=350,
        )
        fog = px.line(
            conteo_grado_filtro.loc[conteo_grado_filtro["eia"] == eia],
            x="item",
            y="prop",
            color="resp",
            markers=True,
            color_discrete_sequence=COLORES,
            hover_name="proceso",
            hover_data=["eia", "descriptor", "criterio", "campo"],
            labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"},
            height=350,
        )
        st.plotly_chart(fig)
        st.plotly_chart(fog)

with tab_servicios:
    conteo_servicio_filtro = conteo_servicio.loc[
        (conteo_servicio["nivel"] == sel_cnt_nivel) &
        (conteo_servicio["grado"] == sel_cnt_grado)
        ]
    st.title("Pendiente")
    for servicio in conteo_servicio_filtro["servicio"].unique():
        st.markdown(f"### {servicio}")
        conteo_serv = conteo_servicio_filtro.loc[conteo_servicio_filtro["servicio"] == servicio]
        plotino = go.Figure()
        for resp in conteo_serv["resp"].unique():
            conteo_resp = conteo_serv.loc[conteo_serv["resp"] == resp]
            plotino.add_trace(go.Bar(
                x=conteo_resp["item"],
                y=conteo_resp["prop"],
                name=resp, 
                text=round(conteo_resp["prop"]),
                marker=dict(color=COLORES_RESP[resp]),
                ))
        plotino.update_layout(
            barmode="relative", 
            height=350,
            margin=dict(t=45),
            )
        st.plotly_chart(plotino)
    st.dataframe(
        conteo_servicio_filtro[["item", "campo", "pda", "descriptor", "criterio"]].drop_duplicates(),
        height=350,
        )