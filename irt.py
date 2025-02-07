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

irt = pd.read_parquet("data/item_irt.parquet")

irt = irt.sort_values("dificultad")
procesos = irt["proceso"].unique()
campos   = irt["campo"].unique()

st.set_page_config(
    page_title="IRT - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

#### Streamlit ####

st.title("IRT Evaluación Diagnóstica 2024")

with st.sidebar:
    sel_nivel = st.selectbox("Nivel", options = NIVELES_GRADO.keys(), index=2)
    sel_grado = st.selectbox("Grado", options = NIVELES_GRADO[sel_nivel])

irt_filtro = irt.loc[
    (irt["nivel"] == sel_nivel) &
    (irt["grado"] == sel_grado)
].sort_values(["proceso", "consigna", "inciso", "criterio_num"])

eia_filtro = irt_filtro["eia"].unique()

with st.sidebar:
    sel_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
    sel_proceso = st.multiselect("Proceso", options = procesos, default=procesos)
    sel_campo   = st.multiselect("Campo formativo", options = campos, default=campos)

medias_filtro = irt_filtro.loc[
    (irt_filtro["eia"].isin(sel_eia)) &
    (irt_filtro["proceso"].isin(sel_proceso)) &
    (irt_filtro["campo"].isin(sel_campo))
]

orden = st.radio(
    "Ordenar por:",
    ["Proceso", "Dificultad", "Reactivo"],
    horizontal=True
    )
if st.checkbox("Limites 0-800"):
    limites_y = [0, 800]
else:
    limites_y = None

for eia in medias_filtro["eia"].unique():
    st.markdown(f"### {eia}")
    irt_filtro_eia = medias_filtro.loc[medias_filtro["eia"] == eia]

    if orden == "Proceso":
        irt_filtro_eia = irt_filtro_eia.sort_values(["proceso", "dificultad"])
    elif orden == "Dificultad":
        irt_filtro_eia = irt_filtro_eia.sort_values("dificultad")
    elif orden == "Reactivo":
        irt_filtro_eia = irt_filtro_eia.sort_values(["consigna", "inciso", "item_clave"])

    figura = go.Figure(go.Scatter(
        x=irt_filtro_eia["item_clave"],
        y=irt_filtro_eia["dificultad"],
        mode="lines",
        line=dict(color="#9999bb", width=1),
        showlegend=False,
        ))
    for proceso in irt_filtro_eia["proceso"].unique():
        medias_proceso = irt_filtro_eia.loc[irt_filtro_eia["proceso"] == proceso]
        figura.add_trace(go.Scatter(
            x=medias_proceso["item_clave"],
            y=medias_proceso["dificultad"],
            mode="markers",
            name=proceso,
            marker=dict(color=COLORES_PROCESO[proceso], size=10),
            hovertext=medias_proceso["campo"],
            ))
    figura.update_yaxes(range=limites_y)
    st.plotly_chart(figura)
    campos_eia = irt_filtro_eia["campo"].unique()
    st.dataframe(irt_filtro_eia[["item_clave", "proceso", "dificultad", "campo", "pda", "descriptor", "criterio"]])

