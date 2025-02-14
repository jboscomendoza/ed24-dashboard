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

# Diccionario de variables
diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop([
    "fase", "grado", "eia_clave", "pda_grado", 
    "criterio_clave", "peso_max", "ponderador",
    ], axis=1)
rubrica     = pd.read_parquet("data/diccionario_rubrica.parquet")

# data irt 
irt = pd.read_parquet("data/item_irt_eia.parquet")
irt = irt.merge(diccionario, how="inner", on=["item"])


# data_personas
personas = pd.read_parquet("data/personas.parquet")

# Elementos unicos
procesos = irt["proceso"].unique()
campos   = irt["campo"].unique()


#### Streamlit ####
st.set_page_config(
    page_title="Conteos - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

st.title("Perfiles Evaluación Diagnóstica 2024")

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
eia_filtro = irt_filtro["eia"].unique()

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

for eia in irt_filtro["eia"].unique():
    st.markdown(f"## {eia}")
    irt_eia = irt_filtro.loc[irt_filtro["eia"] == eia]
    personas_eia = personas_filtro[personas_filtro["eia"] == eia]
    dificultades = (
        irt_eia
        .sort_values("dificultad")
        ["dificultad"]
        .values.round(2)
    )
    
    sel_dif = st.select_slider(
        "Corte",
        options=dificultades,
        key=f"slider_{eia}"
        )
    sel_texto = st.radio(
        "Texto para mostrar.", 
        options=["Dificultad", "Proceso", "Campo formativo"],
        horizontal=True,
        key=f"texto_{eia}",
        )
    if sel_texto == "Campo formativo":
        sel_texto = "campo_clave"
    else:
        sel_texto = sel_texto.lower()
    
    fig = go.Figure()
    fig.add_hline(
        y=sel_dif,
        line_width=1,
        line_color="#858ae3"
        )
    for resp in irt_eia["resp"].unique():
        irt_resp = irt_eia.loc[irt_eia["resp"] == resp]
        fig.add_trace(go.Scatter(
            x=irt_resp["item"],
            y=irt_resp["dificultad"],
            name=resp,
            mode="markers+text",
            text= round(irt_resp[sel_texto], 2),
            textposition="top center",
            hovertext=irt_resp["criterio"],
            marker=dict(color=COLORES_RESP[resp])
        ))
        fig.update_xaxes(title_text="Criterios")
        fig.update_yaxes(title_text="Dificultad")
        fig.update_layout(
            height=400,
            margin=dict(t=30, b=15),
        )
    
    personas_cuantil = personas_eia.loc[personas_eia["puntaje"] <= float(sel_dif), ["cuantil", "puntaje"]].reset_index(drop=True)
    personas_cuantil["puntaje"] = personas_cuantil["puntaje"].round(3)
    irt_cuantil = irt_eia.sort_values("dificultad")
    irt_cuantil["posicion"] = ["Arriba" if i >= sel_dif else "Abajo" for i in irt_cuantil["dificultad"]]
    irt_cuantil = irt_cuantil[["item", "resp", "dificultad", "posicion", "proceso", "criterio", "descriptor", "campo"]]
    
    st.markdown("### Dificultades de los criterios")
    st.plotly_chart(fig, key=eia)
    st.markdown("### Población debajo del punto de corte.")
    st.dataframe(personas_cuantil.iloc[-1])
    st.markdown("### Posición de los criterios respecto al punto de corte.")
    posiciones = st.multiselect("Mostrar sólo criterios que están:", options=["Arriba", "Abajo"], default=["Arriba", "Abajo"], key=f"posicion_{eia}")
    st.dataframe(irt_cuantil.loc[irt_cuantil["posicion"].isin(posiciones)])