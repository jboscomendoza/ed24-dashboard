import streamlit as st
import polars as pl
import plotly.graph_objects as go

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
}

COLORES = ["#8338ec", "#ffca3a", "#8ac926", "#1982c4", "#cccccc"]
PROCESOS = [
    "Comprensión",
    "Utilización del conocimiento",
    "Propuesta de solución",
    "Juicio crítico",
    "No definido",
]
COLORES_PROCESO = dict(zip(PROCESOS, COLORES))
RUTA_DICCIONARIO = "data/diccionario.parquet"
RUTA_MEDIAS = "data/item_medias.parquet"

st.set_page_config(
    page_title="Medias - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)


@st.cache_data
def leer_medias(ruta_diccionario: str, ruta_medias: str) -> pl.DataFrame:
    """Lee el diccionario y medias de los ítems."""
    diccionario = pl.read_parquet(ruta_diccionario).drop("grado")
    medias = (
        pl.read_parquet(ruta_medias)
        .join(diccionario, how="inner", on="item")
        .sort("media")
    )
    return medias


medias = leer_medias(RUTA_DICCIONARIO, RUTA_MEDIAS)

procesos = medias["proceso"].unique(maintain_order=True)
campos = medias["campo"].unique(maintain_order=True)

#### Streamlit ####
st.title("Medias Evaluación Diagnóstica 2024")

with st.sidebar:
    sel_cnt_nivel = st.selectbox("Nivel", options=NIVELES_GRADO.keys(), index=2)
    sel_cnt_grado = st.selectbox("Grado", options=NIVELES_GRADO[sel_cnt_nivel])

medias_filtro = medias.filter(
    pl.col("nivel") == sel_cnt_nivel,
    pl.col("grado") == sel_cnt_grado,
).sort(["proceso", "consigna", "inciso", "criterio_num"])

eia_filtro = medias_filtro["eia"].unique(maintain_order=True)

with st.sidebar:
    sel_cnt_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
    sel_cnt_proceso = st.multiselect("Proceso", options=procesos, default=procesos)
    sel_cnt_campo = st.multiselect("Campo formativo", options=campos, default=campos)

medias_filtro = medias_filtro.filter(
    pl.col("eia").is_in(sel_cnt_eia),
    pl.col("proceso").is_in(sel_cnt_proceso),
    pl.col("campo").is_in(sel_cnt_campo),
)

orden = st.radio("Ordenar por:", ["Proceso", "Media", "Reactivo"], horizontal=True)
if st.checkbox("Limites 0-3"):
    limites_y = [0, 3]
else:
    limites_y = None

for eia in medias_filtro["eia"].unique():
    st.markdown(f"### {eia}")
    medias_filtro_eia = medias_filtro.filter(pl.col("eia") == eia)

    if orden == "Proceso":
        medias_filtro_eia = medias_filtro_eia.sort(["proceso", "media"])
    elif orden == "Media":
        medias_filtro_eia = medias_filtro_eia.sort("media", descending=False)
    elif orden == "Reactivo":
        medias_filtro_eia = medias_filtro_eia.sort(["consigna", "inciso", "item"])

    figura = go.Figure(
        go.Scatter(
            x=medias_filtro_eia["item"],
            y=medias_filtro_eia["media"],
            mode="lines",
            line=dict(color="#9999bb", width=1),
            showlegend=False,
        )
    )
    for proceso in medias_filtro_eia["proceso"].unique():
        medias_proceso = medias_filtro_eia.filter(
            medias_filtro_eia["proceso"] == proceso
        )
        figura.add_trace(
            go.Scatter(
                x=medias_proceso["item"],
                y=medias_proceso["media"],
                mode="markers",
                name=proceso,
                marker=dict(color=COLORES_PROCESO[proceso], size=10),
                hovertext=medias_proceso["campo"],
            )
        )
    figura.update_yaxes(range=limites_y)
    figura.update_layout(
        margin=dict(t=20),
    )
    st.plotly_chart(figura)
    if st.checkbox("Mostrar información", key=f"check_tabla_{eia}"):
        st.dataframe(
            medias_filtro_eia.select(
                ["item", "proceso", "media", "campo", "pda", "descriptor", "criterio"]
            ).rename(str.capitalize)
        )
