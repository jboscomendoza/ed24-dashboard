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

COLORES = ["#fcb1c3", "#fce397", "#bae673", "#a4dafc"]
COLORES_RESP = dict(zip(["N0", "N1", "N2", "N3"], COLORES))

COLS_INFORMACION = ["campo", "contenido", "pda", "descriptor", "proceso"]

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

conteo_grado["consigna"] = conteo_grado["consigna"].astype("int").astype("str")
conteo_grado["grado"] = conteo_grado["grado"].astype("int").astype("str")


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

    consignas = conteo_filtro["consigna"].unique()
    consignas.sort()
    sel_consigna = st.selectbox("Consigna", options=consignas)
    conteo_filtro = conteo_filtro.loc[conteo_filtro["consigna"] == sel_consigna]

st.markdown(f"# {conteo_filtro["eia"].unique()[0]} (Consigna {sel_consigna})")

criterios = conteo_filtro["criterio"].unique()
sel_criterios = st.multiselect("Criterios",options=criterios, default=criterios)
conteo_filtro = conteo_filtro.loc[conteo_filtro["criterio"].isin(sel_criterios)]


for criterio in sel_criterios:
    st.divider()
    st.markdown(f"## {criterio}")
    conteo_criterio = conteo_filtro.loc[conteo_filtro["criterio"] == criterio]

    figura = go.Figure()
    for resp in conteo_criterio["resp"].unique():
        conteo_resp = conteo_criterio.loc[conteo_criterio["resp"] == resp]
        figura.add_trace(go.Bar(
            y=conteo_resp["grado"],
            x=conteo_resp["prop"],
            name=resp,
            text=round(conteo_resp["prop"]),
            insidetextanchor="middle",
            marker=dict(color=COLORES_RESP[resp]),
            orientation="h",
        ))
    figura.update_layout(
        barmode="stack",
        height=225,
        width=600,
        margin=dict(t=30, b=30),
        yaxis=dict(
            title="Grado",
            tickmode='array',
            tickvals = conteo_criterio["grado"],
            ticktext = conteo_criterio["grado"].unique(),
            autorange="reversed",
            ),
        xaxis=dict(title="Porcentaje"),
        font=dict(family="Noto Sans, serif", size=16)
        )
    st.plotly_chart(figura)
    
    st.markdown(f"### Información del criterio")
    st.table((
        conteo_criterio[COLS_INFORMACION]
        .rename(str.title, axis="columns")
        .drop_duplicates()
        .reset_index(drop=True)
        ))
    conteo_criterio = (
        conteo_criterio[["resp", "resp_nivel", "resp_rubrica"]]
        .drop_duplicates()
        .rename(columns={"resp":"Respuesta", "resp_nivel":"Nivel", "resp_rubrica":"Rúbrica"})
        .reset_index(drop=True)
        )
    st.markdown(f"### Niveles de la rúbrica")
    st.table(conteo_criterio)