import streamlit as st
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 3],
}
COLORES_RESP = dict(
    zip(["N0", "N1", "N2", "N3"], ["#fcb1c3", "#ef476f", "#f5b700", "#008bf8"])
)
COLUMNAS_TABLA = [
    "item",
    "resp",
    "dificultad",
    "posicion",
    "criterio",
    "proceso",
    "campo",
    "descriptor",
]
COLOR_LINEA = "#9b5de5"
COLOR_BARRA = "#bfd3c1"
RUTA_DICCIONARIO = "data/diccionario.parquet"
RUTA_PERSONAS = "data/personas_uni.parquet"
RUTA_PERSONAS_DIST = "data/personas_dist.parquet"
RUTA_IRT = "data/item_irt_eia.parquet"
DROP_DICCIONARIO = [
    "fase",
    "grado",
    "eia_clave",
    "pda_grado",
    "criterio_clave",
    "peso_max",
    "ponderador",
]

st.set_page_config(
    page_title="Perfiles - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)


@st.cache_data
def leer_irt(ruta_diccionario: str, ruta_irt: str) -> pl.DataFrame:
    """Diccionario de variables y lectura de irt."""
    diccionario = pl.read_parquet(RUTA_DICCIONARIO).drop(DROP_DICCIONARIO)
    irt = pl.read_parquet(RUTA_IRT).join(diccionario, how="inner", on=["item"])
    return irt


@st.cache_data
def leer_personas(ruta_personas: str) -> pl.DataFrame:
    """Lectura de personas."""
    personas = pl.read_parquet(RUTA_PERSONAS)
    return personas


@st.cache_data
def leer_personas_dist(ruta_personas_dist: str) -> pl.DataFrame:
    """Lectira de distribución de personas."""
    personas_dist = pl.read_parquet(ruta_personas_dist)
    return personas_dist


irt = leer_irt(RUTA_DICCIONARIO, RUTA_IRT)
personas = leer_personas(RUTA_PERSONAS)
personas_dist = leer_personas_dist(RUTA_PERSONAS_DIST)

# Elementos unicos
procesos = irt["proceso"].unique()
campos = irt["campo"].unique()

#### Streamlit ####
st.title("Perfiles Evaluación Diagnóstica 2024")

# Filtro de niveles y grado
niveles = personas["nivel"].unique()
with st.sidebar:
    sel_nivel = st.selectbox("Nivel", options=niveles)
    sel_grado = st.selectbox("Grado", options=NIVELES_GRADO[sel_nivel], index=0)
irt_filtro = irt.filter(
    pl.col("nivel") == sel_nivel,
    pl.col("grado") == sel_grado,
).sort(["proceso", "consigna", "inciso", "criterio_num"])
personas_filtro = personas.filter(
    pl.col("nivel") == sel_nivel,
    pl.col("grado") == str(sel_grado),
)
personas_dist_filtro = personas_dist.filter(
    pl.col("nivel") == sel_nivel,
    pl.col("grado") == sel_grado,
)

# Filtro de eia, proceso y campo
with st.sidebar:
    sel_proceso = st.multiselect("Proceso", options=procesos, default=procesos)
    sel_campo = st.multiselect("Campo formativo", options=campos, default=campos)
irt_filtro = irt_filtro.filter(
    pl.col("proceso").is_in(sel_proceso),
    pl.col("campo").is_in(sel_campo),
)

# Genera elementos por cada eia seleccionado
st.markdown(f"## Grado {sel_grado}")

dificultades = irt_filtro.sort("dificultad")["dificultad"].round(2)
# Controles de punto corte
puntaje_min = personas_filtro["puntaje"].min()
puntaje_max = personas_filtro["puntaje"].max()

col_1, col_2 = st.columns([0.7, 0.3])
with col_1:
    sel_dif = st.select_slider(
        "Punto de corte",
        options=dificultades,
    )
    if sel_dif < puntaje_min:
        sel_dif = puntaje_min
# Indicador de población debajo del punto de corte
with col_2:
    personas_cuantil = personas_filtro.filter(
        pl.col("puntaje") <= float(sel_dif)
    ).select(["cuantil", "puntaje"])
    personas_cuantil = personas_cuantil.with_columns(pl.col("puntaje").round(3))
    personas_cuantil_corte = personas_cuantil["cuantil"].last()
    st.metric("Personas debajo del corte.", value=personas_cuantil_corte)
# Subplot mapa de Wright
fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.75, 0.25],
    subplot_titles=["Items", "Personas"],
    shared_yaxes=True,
    horizontal_spacing=0,
)
# Un trace de Scatter por cada nivel de respuesta
for resp in irt_filtro["resp"].unique(maintain_order=True):
    irt_resp = irt_filtro.filter(pl.col("resp") == resp)
    fig.add_trace(
        go.Scatter(
            x=irt_resp["item"],
            y=irt_resp["dificultad"],
            name=resp,
            mode="markers+text",
            text=irt_resp["dificultad"].round().cast(pl.String),
            textposition="top center",
            hovertext=(
                irt_resp["criterio"].cast(pl.String)
                + "<br>"
                + irt_resp["proceso"].cast(pl.String)
                + "<br>"
                + irt_resp["campo"].cast(pl.String)
            ),
            marker=dict(color=COLORES_RESP[resp]),
        ),
        row=1,
        col=1,
    )
fig.update_xaxes(title_text="Criterios", row=1, col=1)
fig.update_yaxes(title_text="Dificultad")
# Trace de personas, en modo vertical
# personas_dist_filtro
personas_dist_filtro = personas_dist_filtro.filter(
    pl.col("dificultad").is_between(
        puntaje_min,
        puntaje_max,
        closed="none",
    )
)

fig.add_trace(
    go.Bar(
        x=personas_dist_filtro["conteo"],
        y=personas_dist_filtro["dificultad"],
        marker=dict(color=COLOR_BARRA),
        orientation="h",
        showlegend=False,
    ),
    row=1,
    col=2,
)
fig.update_xaxes(title_text="Conteo", row=1, col=2)
fig.update_yaxes(title_text="Habilidad", side="right", row=1, col=2)
# Lineas horizontales en scatter y bar
fig.add_hline(y=sel_dif, line_width=1.5, line_color=COLOR_LINEA, row=1, col=2)
fig.add_hline(
    y=sel_dif,
    line_width=1.5,
    line_color=COLOR_LINEA,
    row=1,
    col=1,
)
# Layout general del subplot
fig.update_layout(
    barmode="group",
    bargap=0.0,
    height=500,
    margin=dict(t=25, b=15),
)
st.plotly_chart(fig)
# Criterios arriba y debajo del corte
if st.checkbox("Mostrar tabla de criterios.", value=False):
    irt_cuantil = irt_filtro.sort("dificultad")
    posiciones = [
        "Arriba" if i >= sel_dif else "Abajo" for i in irt_cuantil["dificultad"]
    ]
    irt_cuantil = irt_cuantil.with_columns(
        pl.col("dificultad").round(3),
        posicion=pl.Series(posiciones),
    )
    st.markdown("### Posición de los criterios respecto al punto de corte.")
    posiciones = st.multiselect(
        "Mostrar sólo criterios que están:",
        options=["Arriba", "Abajo"],
        default=["Arriba", "Abajo"],
    )
    irt_cuantil = irt_cuantil[COLUMNAS_TABLA]
    st.dataframe(irt_cuantil.filter(pl.col("posicion").is_in(posiciones)))
# Tabla de cuantiles de personas
if st.checkbox("Mostrar cuantiles de personas.", value=False):
    st.markdown("### Cuantiles de habilidades de las personas.")
    persona_tabla = (
        personas.filter(pl.col("grado") == str(sel_grado))
        .with_columns(pl.col("puntaje").round(2))
        .select(["cuantil", "puntaje"])
        .to_pandas()
        .reset_index(drop=True)
        .transpose()
    )
    st.table(persona_tabla)
