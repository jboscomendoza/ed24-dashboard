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
COLORES_RESP = dict(zip(
    ["N0", "N1", "N2", "N3"], 
    ["#fcb1c3", "#ef476f", "#f5b700", "#008bf8"]
    ))
COLUMNAS_TABLA = [
    "item", "resp", "dificultad", "posicion", "criterio", "proceso", 
    "campo", "descriptor"
    ]
COLOR_LINEA = "#9b5de5"
COLOR_BARRA = "#bfd3c1"

# Diccionario de variables
diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop([
    "fase", "grado", "eia_clave", "pda_grado", 
    "criterio_clave", "peso_max", "ponderador",
    ], axis=1)
### rubrica = pd.read_parquet("data/diccionario_rubrica.parquet")
# Data irt 
irt = pd.read_parquet("data/item_irt_eia.parquet")
irt = irt.merge(diccionario, how="inner", on=["item"])
# Data personas
personas = pd.read_parquet("data/personas.parquet")
personas_dist = pd.read_parquet("data/personas_dist.parquet")
# Elementos unicos
procesos = irt["proceso"].unique()
campos   = irt["campo"].unique()

#### Streamlit ####
st.set_page_config(
    page_title="Perfiles - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)
st.title("Perfiles Evaluación Diagnóstica 2024")
# Filtro de niveles y grado
with st.sidebar:
    sel_nivel = st.selectbox("Nivel", options = NIVELES_GRADO.keys(), index=2)
    sel_grado = st.selectbox("Grado", options = NIVELES_GRADO[sel_nivel], index=0)
irt_filtro = irt.loc[
    (irt["nivel"] == sel_nivel) &
    (irt["grado"] == sel_grado)
    ].sort_values(["proceso", "consigna", "inciso", "criterio_num"])
personas_filtro = personas.loc[
    (personas["nivel"] == sel_nivel) &
    (personas["grado"] == sel_grado)
    ]
personas_dist_filtro = personas_dist.loc[
    (personas_dist["nivel"] == sel_nivel) &
    (personas_dist["grado"] == sel_grado)
]
eia_filtro = irt_filtro["eia"].unique()
# Filtro de eia, proceso y campo
with st.sidebar:
    sel_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
    sel_proceso = st.multiselect("Proceso", options=procesos, default=procesos)
    sel_campo = st.multiselect("Campo formativo", options=campos, default=campos)
irt_filtro = irt_filtro.loc[
    (irt_filtro["eia"].isin(sel_eia)) &
    (irt_filtro["proceso"].isin(sel_proceso)) &
    (irt_filtro["campo"].isin(sel_campo))
    ]
personas_filtro = personas_filtro[(
    personas_filtro["eia"].isin(sel_eia)
    )]
personas_dist_filtro = personas_dist_filtro[(
    personas_dist_filtro["eia"].isin(sel_eia)
    )]
# Genera elementos por cada eia seleccionado
for eia in irt_filtro["eia"].unique():
    st.markdown(f"## {eia}")
    irt_eia = irt_filtro.loc[irt_filtro["eia"] == eia]
    personas_eia = personas_filtro[personas_filtro["eia"] == eia]
    personas_dist_eia = personas_dist_filtro[personas_dist_filtro["eia"] == eia]
    dificultades = (
        irt_eia
        .sort_values("dificultad")
        .loc[:, "dificultad"]
        .values.round(2)
    )
    # Controles de punto corte
    col_1, col_2 = st.columns([0.7, 0.3])
    with col_1:
        sel_dif = st.select_slider(
            "Punto de corte",
            options=dificultades,
            key=f"slider_{eia}"
            )
        if sel_dif < 0:
            sel_dif = 0 
    # Indicador de población debajo del punto de corte
    with col_2:
        personas_cuantil = (
            personas_eia
            .loc[personas_eia["puntaje"] <= float(sel_dif), ["cuantil", "puntaje"]]
            .reset_index(drop=True)
            )
        personas_cuantil.loc[:,"puntaje"] = personas_cuantil.loc[:,"puntaje"].round(3)
        personas_cuantil_corte = personas_cuantil.iloc[-1]["cuantil"]
        st.metric("Personas debajo del corte.", value=personas_cuantil_corte)
    # Subplot mapa de Wright
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.75, 0.25],
        subplot_titles=["Items", "Personas"],
        shared_yaxes=True,
        horizontal_spacing=0,
        )
    # Un trace de Scatter por cada nivel de respuesta
    for resp in irt_eia["resp"].unique():
        irt_resp = irt_eia.loc[irt_eia["resp"] == resp]
        fig.add_trace(go.Scatter(
            x=irt_resp["item"],
            y=irt_resp["dificultad"],
            name=resp,
            mode="markers+text",
            text= irt_resp["dificultad"].round().astype(str),
            textposition="top center",
            hovertext= (
                irt_resp["criterio"].astype(str) + 
                "<br>" + 
                irt_resp["proceso"].astype("str") + 
                "<br>" + 
                irt_resp["campo"].astype("str")
                ),
            marker=dict(color=COLORES_RESP[resp])
        ),
        row=1, col=1)
    fig.update_xaxes(
        title_text="Criterios",
        row=1, col=1
        )
    fig.update_yaxes(title_text="Dificultad")
    # Trace de personas, en modo vertical
    fig.add_trace(go.Bar(
        x=personas_dist_eia["conteo"],
        y=personas_dist_eia["dificultad"],
        marker=dict(color=COLOR_BARRA),
        orientation="h",
        showlegend=False,
        ),
        row=1, col=2
        )
    fig.update_xaxes(
        title_text="Conteo",
        row=1, col=2
        )
    fig.update_yaxes(
        title_text="Habilidad", side="right",
        row=1, col=2
        )
    # Lineas horizontales en scatter y bar
    fig.add_hline(
        y=sel_dif,
        line_width=1.5,
        line_color=COLOR_LINEA,
        row=1, col=2
        )
    fig.add_hline(
        y=sel_dif,
        line_width=1.5,
        line_color=COLOR_LINEA,
        row=1, col=1,
        )
    # Layout general del subplot
    fig.update_layout(
        barmode="group",
        bargap=0.0,
        height=500,
        margin=dict(t=25, b=15),
    )
    st.plotly_chart(fig, key=f"subplot_{eia}")
    # Criterios arriba y debajo del corte
    if st.checkbox(
        "Mostrar tabla de criterios.",
        value=False,
        key=f"check_tabla_{eia}"
        ):
        irt_cuantil = irt_eia.sort_values("dificultad")
        irt_cuantil.loc[:,"posicion"] = ["Arriba" if i >= sel_dif else "Abajo" for i in irt_cuantil["dificultad"]]
        st.markdown("### Posición de los criterios respecto al punto de corte.")
        posiciones = st.multiselect(
            "Mostrar sólo criterios que están:",
            options=["Arriba", "Abajo"],
            default=["Arriba", "Abajo"], key=f"posicion_{eia}"
            )
        irt_cuantil = irt_cuantil[COLUMNAS_TABLA]
        st.dataframe(irt_cuantil.loc[irt_cuantil["posicion"].isin(posiciones)])
    # Tabla de cuantiles de personas
    if st.checkbox(
        "Mostrar cuantiles de personas.",
        value=False,
        key=f"check_tabla_persona_{eia}"
        ):
        persona_tabla = personas_eia
        persona_tabla.loc[:,"puntaje"] = persona_tabla.loc[:,"puntaje"].round(2)
        persona_tabla = (
            persona_tabla[["cuantil", "puntaje"]]
            .reset_index(drop=True)
            .transpose()
            )
        st.markdown("### Cuantiles de habilidades de las personas.")
        st.table(persona_tabla)