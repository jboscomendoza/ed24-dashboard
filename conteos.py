import pyarrow
import streamlit as st
import pandas as pd
import plotly.express as px

diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop(["fase", "nivel", "grado"], axis=1)

conteo_grado = pd.read_parquet("data/item_conteo_grado.parquet")
conteo_grado = conteo_grado.merge(diccionario, how="inner", on="item")
conteo_grado["resp"] = conteo_grado["resp"].astype("category").cat.reorder_categories(["N0", "N1", "N2", "N3"], ordered=True)

conteo_servicio = pd.read_parquet("data/item_conteo_servicio.parquet")

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

COLORES = ["#ff595e", "#ffca3a", "#8ac926", "#1982c4"]

#### Streamlit ####

st.set_page_config(
    page_title="Conteos Evaluación diagnóstica 2024",
    page_icon=":book:",
    #layout="wide",
)

st.title("Conteos Evalución Diagnóstica 2024")

tab_grado, tab_servicio = st.tabs(["Grado", "Servicio"])

with tab_grado:
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
    ].sort_values(["proceso", "consigna", "inciso", "criterio_num"])

    for eia in conteo_grado_filtro["eia"].unique():
        st.markdown(f"### {eia}")
        fig = px.bar(
            conteo_grado_filtro.loc[conteo_grado_filtro["eia"] == eia],
            x="item",
            y="prop",
            color="resp",
            color_discrete_sequence=COLORES,
            hover_name="proceso",
            hover_data=["eia", "descriptor", "criterio", "campo"],
            labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"},
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
        )
        st.plotly_chart(fig)
        st.plotly_chart(fog)
