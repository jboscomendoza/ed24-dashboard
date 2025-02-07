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

COLORES = ["#8338ec", "#ffca3a", "#8ac926", "#1982c4"]
COLORES_PROCESO = {
    "Recuperación de información":"#ff595e",
    "Comprensión":"#ffca3a",
    "Análisis":"#8ac926",
    "Utilización del conocimiento":"#1982c4",
    "No definido":"#ffffff",
}

diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop(["grado"], axis=1)

medias = pd.read_parquet("data/item_medias.parquet")
medias = medias.merge(diccionario, how="inner", on="item")
medias = medias.sort_values("media")
procesos = medias["proceso"].unique()
campos   = medias["campo"].unique()

st.set_page_config(
    page_title="Medias - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

#### Streamlit ####

st.title("Medias Evaluación Diagnóstica 2024")

with st.sidebar:
    sel_cnt_nivel = st.selectbox("Nivel", options = NIVELES_GRADO.keys(), index=2)
    sel_cnt_grado = st.selectbox("Grado", options = NIVELES_GRADO[sel_cnt_nivel])

medias_filtro = medias.loc[
    (medias["nivel"] == sel_cnt_nivel) &
    (medias["grado"] == sel_cnt_grado)
].sort_values(["proceso", "consigna", "inciso", "criterio_num"])

eia_filtro = medias_filtro["eia"].unique()

with st.sidebar:
    sel_cnt_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
    sel_cnt_proceso = st.multiselect("Proceso", options = procesos, default=procesos)
    sel_cnt_campo   = st.multiselect("Campo formativo", options = campos, default=campos)

medias_filtro = medias_filtro.loc[
    (medias_filtro["eia"].isin(sel_cnt_eia)) &
    (medias_filtro["proceso"].isin(sel_cnt_proceso)) &
    (medias_filtro["campo"].isin(sel_cnt_campo))
]

orden = st.radio(
    "Ordenar por:",
    ["Proceso", "Media", "Reactivo"],
    horizontal=True
    )
if st.checkbox("Limites 0-3"):
    limites_y = [0, 3]
else:
    limites_y = None

for eia in medias_filtro["eia"].unique():
    st.markdown(f"### {eia}")
    medias_filtro_eia = medias_filtro.loc[medias_filtro["eia"] == eia]

    if orden == "Proceso":
        medias_filtro_eia = medias_filtro_eia.sort_values(["proceso", "media"])
    elif orden == "Media":
        medias_filtro_eia = medias_filtro_eia.sort_values("media", ascending=False)
    elif orden == "Reactivo":
        medias_filtro_eia = medias_filtro_eia.sort_values(["consigna", "inciso", "item"])

    figura = go.Figure(go.Scatter(
        x=medias_filtro_eia["item"],
        y=medias_filtro_eia["media"],
        mode="lines",
        line=dict(color="#ffffff", width=1),
        showlegend=False,
        ))
    for proceso in medias_filtro_eia["proceso"].unique():
        medias_proceso = medias_filtro_eia.loc[medias_filtro_eia["proceso"] == proceso]
        figura.add_trace(go.Scatter(
            x=medias_proceso["item"],
            y=medias_proceso["media"],
            mode="markers",
            name=proceso,
            marker=dict(color=COLORES_PROCESO[proceso], size=10),
            hovertext=medias_proceso["campo"],
            ))
    figura.update_yaxes(range=limites_y)
    st.plotly_chart(figura)
    campos_eia = medias_filtro_eia["campo"].unique()
    st.dataframe(medias_filtro_eia[["item", "proceso", "media", "campo", "pda", "descriptor", "criterio"]])

