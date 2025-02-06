import pyarrow
import streamlit as st
import pandas as pd
import plotly.express as px

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
    }

COLORES = ["#8338ec", "#ffca3a", "#8ac926", "#1982c4"]

diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop(["grado"], axis=1)

medias = pd.read_parquet("data/item_medias.parquet")
medias = medias.merge(diccionario, how="inner", on="item")
medias = medias.sort_values("media")
procesos = medias["proceso"].unique()

st.set_page_config(
    page_title="Conteos Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

#### Streamlit ####

st.title("Medias Evalución Diagnóstica 2024")

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

medias_filtro = medias_filtro.loc[
    (medias_filtro["eia"].isin(sel_cnt_eia)) &
    (medias_filtro["proceso"].isin(sel_cnt_proceso))
]

orden = st.radio("Ordenar por:", ["Proceso", "Media en la rúbrica"])
if orden == "Media en la rúbrica":
#if por_media:
    medias_filtro = medias_filtro.sort_values(["media", "proceso", "consigna", "inciso", "criterio_num"], ascending=False)

for eia in medias_filtro["eia"].unique():
    st.markdown(f"### {eia}")
    medias_filtro_eia = medias_filtro.loc[medias_filtro["eia"] == eia]
    fig = px.line(
        medias_filtro_eia,
        x="item",
        y="media",
        text="proceso",
        markers=True,
        color_discrete_sequence=COLORES,
        hover_name="proceso",
        hover_data=["eia", "descriptor", "criterio", "campo"],
        labels={"media":"Media en la rúbrica", "item":"Criterio"},
    )
    st.plotly_chart(fig)
    st.dataframe(medias_filtro_eia[["item", "proceso", "media", "campo", "pda", "descriptor", "criterio"]])