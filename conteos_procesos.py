import pyarrow
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
    }

COLORES = ["#fcb1c3", "#fce397", "#bae673", "#a4dafc"]
COLORES_RESP = dict(zip(["N0", "N1", "N2", "N3"], COLORES))

COLS_INFORMACION = ["campo", "contenido", "pda", "descriptor", "criterio"]

diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop(["fase", "nivel", "grado"], axis=1)
rubrica     = pd.read_parquet("data/diccionario_rubrica.parquet")

conteo_grado = pd.read_parquet("data/item_conteo_grado.parquet")
conteo_grado = (
    conteo_grado
    .merge(diccionario, how="inner", on="item")
    .merge(rubrica, how="inner", on=["item", "resp"])
    )

conteo_grado["resp"] = (
    conteo_grado["resp"]
    .astype("category")
    .cat
    .reorder_categories(["N0", "N1", "N2", "N3"], ordered=True)
)

conteo_grado["consigna"] = conteo_grado["consigna"].astype("int").astype("string")
conteo_grado["grado"] = conteo_grado["grado"].astype("int").astype("string")


nivel_0 = (
    conteo_grado
    .loc[conteo_grado["resp"] == "N0"][["item", "grado", "prop"]]
    .rename(columns={"prop":"nivel_0"})
    )
nivel_3 = (
    conteo_grado
    .loc[conteo_grado["resp"] == "N3"][["item", "grado", "prop"]]
    .rename(columns={"prop":"nivel_3"})
    )
conteo_grado = (
    conteo_grado
    .merge(nivel_0, on=["item", "grado"], how="left")
    .merge(nivel_3, on=["item", "grado"], how="left")
    )

#### Streamlit ####

st.set_page_config(
    page_title="Conteos por criterio - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

with st.sidebar:
    niveles = conteo_grado["nivel"].unique()
    sel_nivel = st.selectbox("Nivel", options=niveles, index=2)
    conteo_filtro = conteo_grado.loc[conteo_grado["nivel"] == sel_nivel]

    eias = conteo_filtro["eia"].unique()
    sel_eia = st.selectbox("EIA", options=eias)
    conteo_filtro = conteo_filtro.loc[conteo_filtro["eia"] == sel_eia]
    
    procesos = conteo_filtro["proceso"].unique()
    sel_proceso = st.selectbox("Proceso", options=procesos)
    conteo_filtro = conteo_filtro.loc[conteo_filtro["proceso"] == sel_proceso]


st.markdown(f"# {sel_proceso}")

criterios = conteo_filtro["criterio"].unique()
sel_criterios = st.multiselect("Criterios",options=criterios, default=criterios)
conteo_filtro = conteo_filtro.loc[conteo_filtro["criterio"].isin(sel_criterios)]

num_criterios = len(sel_criterios)
figura = make_subplots(
    rows=1, 
    cols=num_criterios,
    subplot_titles=sel_criterios,
    x_title="Grado",
    y_title="Porcentaje",
    shared_xaxes=True,
    shared_yaxes=True,
    )

for id_criterio in range(num_criterios):
    criterio = sel_criterios[id_criterio]
    conteo_criterio = conteo_filtro.loc[conteo_filtro["criterio"] == criterio]

    for resp in conteo_criterio["resp"].unique():
        conteo_resp = conteo_criterio.loc[conteo_criterio["resp"] == resp]
        figura.add_trace(go.Bar(
            x=conteo_resp["grado"].astype("string"),
            y=conteo_resp["prop"],
            name=resp,
            legendgroup="group",
            text=round(conteo_resp["prop"]),
            insidetextanchor="middle",
            marker=dict(color=COLORES_RESP[resp],),
            ),
            row=1, col=id_criterio+1
            )
        if id_criterio != num_criterios-1:
            figura.update_traces(
                showlegend=False,
            )
figura.update_xaxes(
    title="",
    type="category",
)
figura.update_yaxes(
    title="",
)
figura.update_layout(
    barmode="stack",
    height=375,
    width=175*num_criterios,
    margin=dict(t=35, b=30),
    font=dict(family="Noto Sans, serif", size=16),
    )
st.plotly_chart(figura, use_container_width=False)
    
st.markdown(f"### Información del proceso")
st.table((
    conteo_filtro[COLS_INFORMACION]
    .rename(str.title, axis="columns")
    .drop_duplicates()
    .reset_index(drop=True)
    ))
conteo_criterio = (
    conteo_filtro[["resp", "resp_nivel", "resp_rubrica"]]
    .drop_duplicates()
    .rename(columns={"resp":"Respuesta", "resp_nivel":"Nivel", "resp_rubrica":"Rúbrica"})
    .reset_index(drop=True)
    )
st.markdown(f"### Niveles de la rúbrica")
st.table(conteo_criterio)