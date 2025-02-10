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
    page_title="Conteos por criterio- Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

st.title("Conteos Evaluación Diagnóstica 2024")

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

criterios = conteo_filtro["criterio"].unique()

sel_criterios = st.multiselect("Criterios",options=criterios, default=criterios)
conteo_filtro = conteo_filtro.loc[conteo_filtro["criterio"].isin(sel_criterios)]

for criterio in sel_criterios:
    st.markdown(f"## {criterio}")
    conteo_criterio = conteo_filtro.loc[conteo_filtro["criterio"] == criterio]
    grados = conteo_criterio["grado"].unique()
    num_grados = len(grados)
    columns = st.columns(num_grados+1)
    for i in range(num_grados+1):
        if i < num_grados:
            with columns[i]:
                st.markdown(f"### Grado {grados[i]}")
                fig = go.Figure()
                conteo_grado = conteo_criterio.loc[conteo_criterio["grado"] == grados[i]]
                resps = conteo_grado["resp"].unique()
                for resp in resps:
                    conteo_resp = conteo_grado.loc[conteo_grado["resp"] == resp] 
                    fig.add_trace(go.Bar(
                        x=conteo_resp["item"],
                        y=conteo_resp["prop"],
                        text=round(conteo_resp["prop"]),
                        name=resp,
                        marker=dict(color = COLORES_RESP[resp]),
                        ))
                fig.update_layout(
                    barmode="stack",
                    margin=dict(t=35),
                    width=275,
                )
                st.plotly_chart(fig)
        else:
            with columns[i]:
                st.markdown(f"### Datos del criterio")
                st.table(
                    conteo_criterio[[
                        "campo", "resp", "descriptor", "proceso", "resp_rubrica"
                        ]].drop_duplicates()
                        )


