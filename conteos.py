import pyarrow
import streamlit as st
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots


NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
}

COLORES_RESP = dict(
    zip(["N0", "N1", "N2", "N3"], ["#fcb1c3", "#fce397", "#bae673", "#a4dafc"])
)

COLS_TABLA = [
    "item",
    "proceso",
    "campo",
    "contenido",
    "pda",
    "descriptor",
    "criterio",
]

#### Streamlit ####
st.set_page_config(
    page_title="Conteos - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)


@st.cache_data
def read_conteo(ruta):
    conteo = pl.read_parquet(ruta)
    return conteo


# Data conteos
conteo = read_conteo("data/st_conteo.parquet")

st.title("Conteos Evaluación Diagnóstica 2024")

with st.sidebar:
    sel_nivel = st.selectbox("Nivel", options=NIVELES_GRADO.keys(), index=2)
    sel_grado = st.selectbox("Grado", options=NIVELES_GRADO[sel_nivel], index=0)

conteo_filtro = conteo.filter(
    pl.col("nivel") == sel_nivel, pl.col("grado") == sel_grado
).sort(["eia", "proceso", "consigna", "inciso", "criterio_num"])

eia_filtro = conteo_filtro["eia"].unique().sort()

st.markdown("**Ordenar por:**")
sel_orden = st.radio(
    "Ordenar por:",
    ["Reactivo", "Proceso", "Campo", "Nivel 0", "Nivel 3"],
    horizontal=True,
    label_visibility="collapsed",
)

for eia in eia_filtro:
    st.markdown(f"### {eia}")

    conteo_eia = conteo_filtro.filter(pl.col("eia") == eia)

    if sel_orden == "Reactivo":
        conteo_eia = conteo_eia.sort(["consigna", "inciso", "item"])
    elif sel_orden == "Proceso":
        conteo_eia = conteo_eia.sort(["proceso", "item"])
    elif sel_orden == "Campo":
        conteo_eia = conteo_eia.sort(["campo", "item"])
    elif sel_orden == "Nivel 0":
        conteo_eia = conteo_eia.sort(["nivel_0", "item"])
    elif sel_orden == "Nivel 3":
        conteo_eia = conteo_eia.sort(["nivel_3", "item"])

    # Generar plot multiple
    plot_medias = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.25, 0.35, 0.40],
        vertical_spacing=0.05,
    )

    # Plot media de puntaje
    plot_medias.add_trace(
        go.Scatter(
            x=conteo_eia["item"],
            y=conteo_eia["media"],
            name="Media",
            mode="lines+markers+text",
            text=conteo_eia["media"].round(2),
            hovertext=conteo_eia["proceso"],
            textposition="top center",
            marker=dict(color="#adb5bd"),
        ),
        row=1,
        col=1,
    )
    plot_medias.update_yaxes(
        title_text="Media",
        range=[0.75, 2.25],
        row=1,
        col=1,
    )
    # Plot Dificultad irt
    for resp in conteo_eia["resp"].unique():
        conteo_irt = conteo_eia.filter(pl.col("resp") == resp).select(
            pl.col(["item", "dificultad", "resp"])
        )
        plot_medias.append_trace(
            go.Scatter(
                x=conteo_irt["item"],
                y=conteo_irt["dificultad"],
                mode="markers+text",
                name=resp,
                text=conteo_irt["dificultad"].round(),
                textposition="middle right",
                marker=dict(color=COLORES_RESP[resp]),
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        plot_medias.update_yaxes(
            title_text="Dificultad",
            row=2,
            col=1,
        )
    # Plot proporcion de niveles
    for resp in conteo_eia["resp"].unique():
        conteo_eia_resp = conteo_eia.filter(pl.col("resp") == resp)
        plot_medias.append_trace(
            go.Bar(
                x=conteo_eia_resp["item"],
                y=conteo_eia_resp["prop"],
                name=resp,
                text=conteo_eia_resp["prop"].round(),
                insidetextanchor="middle",
                marker=dict(color=COLORES_RESP[resp]),
            ),
            row=3,
            col=1,
        )
        plot_medias.update_yaxes(
            title_text="Porcentaje",
            row=3,
            col=1,
        )
    plot_medias.update_layout(
        barmode="stack",
        height=550,
        margin=dict(t=35, b=35),
    )
    st.plotly_chart(plot_medias)

    if st.checkbox("Ver tabla de especificaciones.", value=False, key=f"tabla_{eia}"):
        st.table(conteo_eia.select(pl.col(COLS_TABLA)).unique())