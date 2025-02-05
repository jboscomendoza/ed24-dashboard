import pyarrow
import streamlit as st
import pandas as pd
import plotly.express as px

conteo_grado = pd.read_parquet("data/item_conteo_grado.parquet")
diccionario = pd.read_parquet("data/diccionario.parquet")


NIVELES_FASE = {
    "Preescolar":{
        "2":[3]
        },
    "Primaria":{
        "3":[1, 2],
        "4":[3, 4],
        "5":[5, 6]
    },
    "Secundaria":{
        "6":[1, 2, 3],
    }
}

#### Streamlit ####

st.set_page_config(
    page_title="Conteos Evaluación diagnóstica 2024",
    page_icon=":book:",
    layout="wide",
)

st.title("Conteos Evalución Diagnóstica 2024")

sel_cnt_nivel = st.selectbox("Nivel", options = NIVELES_FASE.keys())
col1, col2 = st.columns(2)
with col1:
    sel_cnt_fase  = st.selectbox("Fase",  options = NIVELES_FASE[sel_cnt_nivel].keys())
with col2:
    sel_cnt_grado = st.selectbox("Grado", options = NIVELES_FASE[sel_cnt_nivel][sel_cnt_fase])

conteo_grado_filtro = conteo_grado.loc[
    (conteo_grado["nivel"] == sel_cnt_nivel) &
    (conteo_grado["fase"] == sel_cnt_fase) &
    (conteo_grado["grado"] == sel_cnt_grado)
]

fig = px.bar(
    conteo_grado_filtro,
    x="prop",
    y="item",
    color="resp",
    color_discrete_sequence=["#f94144", "#f8961e", "#f9c74f", "#43aa8b"],
    #hover_data=["eia", "descriptor", "criterio"],
    labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"}
)

st.plotly_chart(fig)