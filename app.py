import streamlit as st
import pyarrow
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

st.title("Evaluación Diagnóstica 2024")

col1, col2, col3  = st.columns(3)
with col1:
    select_nivel = st.selectbox("Nivel", options = NIVELES_FASE.keys())
with col2:
    select_fase  = st.selectbox("Fase",  options = NIVELES_FASE[select_nivel].keys())
with col3:
    select_grado = st.selectbox("Grado", options = NIVELES_FASE[select_nivel][select_fase])

ed_filtro = ed24.loc[
    (ed24["nivel"] == select_nivel) & 
    (ed24["fase"]  == select_fase) & 
    (ed24["grado"] == select_grado)
    ]

eia_filtro    = ed_filtro["eia"].unique()
campo_filtro = ed_filtro["campo"].unique()
select_eia   = st.multiselect("EIA", eia_filtro, default=eia_filtro)
select_campo = st.multiselect("Campo formativo", campo_filtro, default=campo_filtro)

ed_filtro = ed_filtro.loc[
    (ed_filtro["eia"].isin(select_eia)) &
    (ed_filtro["campo"].isin(select_campo))
    ]

st.markdown("### Dificultad de los criterios")

fig = px.scatter(
    ed_filtro,
    x="item",
    y="dificultad",
    color="item_nivel",
    hover_data=["eia", "descriptor", "criterio"],
    hover_name="campo",
)

st.plotly_chart(fig)