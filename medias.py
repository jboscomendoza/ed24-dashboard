import pyarrow
import streamlit as st
import pandas as pd
import plotly.express as px

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
    }

COLORES = ["#60d394"]

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
    sel_cnt_nivel = st.selectbox("Nivel", options = NIVELES_GRADO.keys())
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

for eia in medias_filtro["eia"].unique():
    st.markdown(f"### {eia}")
    fig = px.line(
        medias_filtro.loc[medias_filtro["eia"] == eia],
        x="item",
        y="media",
        line_group="eia",
        markers=True,
        color_discrete_sequence=COLORES,
        hover_name="proceso",
        hover_data=["eia", "descriptor", "criterio", "campo"],
        labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"},
    )
    st.plotly_chart(fig)