import pyarrow
import streamlit as st
import pandas as pd
import plotly.express as px

ed24 = pd.read_parquet("data/ed24-items.parquet")
#  columnas:
#  ['item', 'item_nivel', 'irt_dificultad', 'irt_dificultad_se',
#  'dificultad', 'grado', 'eia', 'campo_clave', 'pda', 'descriptor',
#  'criterio', 'clave_eia', 'clave_criterio', 'fase', 'nivel_clave',
#  'nivel', 'campo', 'eia_num']

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

#### Streamlit #####

st.set_page_config(
    page_title="Evaluación diagnóstica 2024",
    page_icon=":book:",
    layout="wide",
)

st.title("Evaluación Diagnóstica 2024")

with st.sidebar:
    select_nivel = st.selectbox("Nivel", options = NIVELES_FASE.keys())
    col1, col2 = st.columns(2)
    with col1:
        select_fase  = st.selectbox("Fase",  options = NIVELES_FASE[select_nivel].keys())
    with col2:
        select_grado = st.selectbox("Grado", options = NIVELES_FASE[select_nivel][select_fase])

ed_filtro = ed24.loc[
    (ed24["nivel"] == select_nivel) & 
    (ed24["fase"]  == select_fase) & 
    (ed24["grado"] == select_grado)
    ]

eia_filtro   = ed_filtro["eia"].unique()
campo_filtro = ed_filtro["campo"].unique()

with st.sidebar:
    select_eia   = st.multiselect("EIA", eia_filtro, default=eia_filtro)
    select_campo = st.multiselect("Campo formativo", campo_filtro, default=campo_filtro)

ed_filtro = ed_filtro.loc[
    (ed_filtro["eia"].isin(select_eia)) &
    (ed_filtro["campo"].isin(select_campo))
    ]

st.markdown("## Dificultad de los criterios")
 
fig = px.scatter(
    ed_filtro,
    x="item",
    y="dificultad",
    color="item_nivel",
    hover_data=["eia", "descriptor", "criterio"],
    color_discrete_sequence=["#f94144", "#f9c74f", "#43aa8b"],
    hover_name="campo",
    range_y=[0, 800],
)

st.plotly_chart(fig)

st.markdown("## Contenido de los EIA")
for i in eia_filtro:
    st.markdown(f"### {i}")
    st.table((
        ed_filtro
        .loc[ed_filtro["eia"] == i][["item", "campo", "pda", "descriptor", "criterio"]]
        .drop_duplicates()
        ))
