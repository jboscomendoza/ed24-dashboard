import pyarrow
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from textwrap import wrap

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
    }
COLORES = ["#fcb1c3", "#fce397", "#bae673", "#a4dafc"]
CLAVE_RESP = ["N0", "N1", "N2", "N3"]
DESC_RESP = [
    "Sin evidencias de desarrollo<br>del aprendizaje",
    "Requiere apoyo para desarrollar<br>el aprendizaje",
    "En proceso de desarrollo",
    "Aprendizaje desarrollado",
    ]
#DESC_RESP = ["<br>".join(wrap(i, width=16)) for i in DESC_RESP]
COLORES_RESP = dict(zip(DESC_RESP, COLORES))
COLORES_SERVICIO = dict(zip(
    ["Nacional", "General", "Privada", "Técnica", "Telesecundaria"],
    ["#ffadad", "#fcf6bd", "#d0f4de", "#a9def9", "#e4c1f9"]
))

COLS_INFORMACION = ["campo", "contenido", "pda", "descriptor", "criterio"]

diccionario = pd.read_parquet("data/diccionario.parquet")
diccionario = diccionario.drop(["fase", "nivel", "grado"], axis=1)
rubrica     = pd.read_parquet("data/diccionario_rubrica.parquet")

conteo_grado = pd.read_parquet("data/item_conteo_ponderado.parquet")
conteo_grado = (
    conteo_grado
    .merge(diccionario, how="inner", on="item")
    .merge(rubrica, how="inner", on=["item", "resp"])
    .drop_duplicates()
    )

conteo_grado["resp"] = conteo_grado["resp"].replace(CLAVE_RESP, DESC_RESP)

conteo_grado["resp"] = (
    conteo_grado["resp"]
    .astype("category")
    .cat
    .reorder_categories(DESC_RESP, ordered=True)
)

conteo_grado = conteo_grado.sort_values(["grado", "eia_clave", "proceso"])

conteo_grado["consigna"] = conteo_grado["consigna"].astype("int").astype("string")
conteo_grado["grado"] = conteo_grado["grado"].astype("int").astype("string")

#### Streamlit ####

st.set_page_config(
    page_title="Conteos por criterio - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

with st.sidebar:
    st.markdown("### Únicamente fase 6")
    servicios = conteo_grado["servicio"].unique()
    sel_servicio = st.selectbox("Servicio", options=servicios, index=0)
    conteo_filtro = conteo_grado.loc[conteo_grado["servicio"] == sel_servicio]

    eias = conteo_filtro["eia"].unique()
    sel_eia = st.selectbox("EIA", options=eias)
    conteo_filtro = conteo_filtro.loc[conteo_filtro["eia"] == sel_eia]
    
    procesos = conteo_filtro["proceso"].unique()
    sel_proceso = st.multiselect("Proceso", options=procesos, default=procesos)
    conteo_filtro = conteo_filtro.loc[conteo_filtro["proceso"].isin(sel_proceso)]

st.title(f"{sel_eia}")

for proceso in sel_proceso:
    conteo_proceso = conteo_filtro.loc[conteo_filtro["proceso"] == proceso]
    st.markdown(f"## {proceso}")
    
    num_grados = len(conteo_proceso["grado"].unique())
    
    criterios = conteo_proceso["criterio"].unique()
    num_criterios = len(criterios)
    
    if num_grados > 1:
        ancho_col = 70
        ancho_lab = 24
    else:
        ancho_col = 80
        ancho_lab = 18
    ancho_plot = (ancho_col * num_grados * num_criterios) + 70
    nom_criterios = [
        "<br>".join(wrap(i, width = ancho_lab, max_lines=3, placeholder="...")) 
        for i in criterios
        ]

    figura = make_subplots(
        rows=1, 
        cols=num_criterios,
        subplot_titles= nom_criterios,
        x_title="Grado",
        y_title="Porcentaje",
        shared_xaxes=True,
        shared_yaxes=True,
        )
    for id_criterio in range(num_criterios):
        criterio = criterios[id_criterio]
        conteo_criterio = conteo_proceso.loc[
            conteo_proceso["criterio"] == criterio
            ]

        for resp in conteo_criterio["resp"].unique():
            conteo_resp = conteo_criterio.loc[conteo_criterio["resp"] == resp]
            figura.add_trace(go.Bar(
                x=conteo_resp["grado"].astype("string"),
                y=conteo_resp["prop"],
                name=resp,
                #legendgroup="group",
                showlegend=False,
                text=round(conteo_resp["prop"], 1),
                hovertext=conteo_resp["campo"] + 
                    "<br>Consigna " + 
                    conteo_resp["consigna"] + 
                    "<br>Inciso " + 
                    conteo_resp["inciso"],
                insidetextanchor="middle",
                marker=dict(color=COLORES_RESP[resp],),
                ),
                row=1, col=id_criterio+1
                )
            #if id_criterio != num_criterios-1:
            #    figura.update_traces(
            #        showlegend=False,
            #    )
    figura.update_xaxes(
        title="",
        type="category",
    )
    figura.update_yaxes(
        title="",
    )
    figura.update_annotations(
        font_size=12,
        font_family="Noto Sans Condensed, sans",
    )
    figura.update_layout(
        barmode="stack",
        height=400,
        width=ancho_plot,
        margin=dict(t=60, b=25),
        font=dict(
            family="Noto Sans Condensed",
            size=12
            ),
        legend_font_size=11,
        legend_font_family="Noto Sans Condensed",
        legend=dict(
            yref="container",
            y=1.1,
            orientation="h",
        ),
        )
    st.plotly_chart(figura, use_container_width=False)

    if st.checkbox("Mostrar tabla de datos.", key=f"tabla_datos_{criterio}"):
        st.markdown(f"### Tabla de datos")
        tabla_prop = (
            conteo_proceso
            .round({"prop":1})
            .pivot_table(
                index=["criterio", "grado"],
                columns="resp",
                values="prop",
                observed=True,
                )
            .reset_index(names=["criterio", "grado"])
            .rename(columns=str.title)
            )
        st.dataframe(tabla_prop)

    if st.checkbox(
        "Mostrar información del proceso.",
        key=f"check_info_{proceso}"):
        st.markdown(f"### Información del proceso")
        sel_cols = st.multiselect(
            "Columnas para mostrar:", 
            options=COLS_INFORMACION,
            default=COLS_INFORMACION,
            )
        st.table((
            conteo_proceso[sel_cols]
            .rename(str.title, axis="columns")
            .drop_duplicates()
            .reset_index(drop=True)
            ))

    if st.checkbox(
        "Mostrar niveles de la rúbrica.",
        key=f"check_rubrica_{proceso}"
        ):
        st.markdown(f"### Niveles de la rúbrica")
        sel_criterios = st.selectbox("Criterio",options=criterios, index=0)
        conteo_criterio = (
            conteo_proceso[["consigna", "inciso", "resp", "resp_rubrica"]]
            .loc[
                (conteo_proceso["criterio"] == sel_criterios) &
                (conteo_proceso["resp"]!="N0")
                ]
            .drop_duplicates()
            .rename(columns={
                "consigna":"Consigna",
                "inciso":"Inciso",
                "criterio":"Criterio",
                "resp":"Nivel",
                "resp_nivel":"Descripcion",
                "resp_rubrica":"Rúbrica"
                })
            .reset_index(drop=True)
            )
        st.table(conteo_criterio)

comp = conteo_grado.loc[conteo_grado["eia"] == sel_eia]
criterios_comp = comp["criterio"].unique()
grados_comp = comp["grado"].unique()
    
st.markdown("## Comparativos")
if st.checkbox("Mostrar comparativos."):
    sel_grado = st.selectbox("Grado", options=grados_comp)
    for criterio in criterios_comp:
        st.markdown(f"### {criterio}")
        comp_criterio = comp.loc[(comp["criterio"] == criterio) & (comp["grado"] == sel_grado)]
        fig_crit = go.Figure()
        for servicio in servicios:
            comp_serv = comp_criterio.loc[comp_criterio["servicio"] == servicio]
            fig_crit.add_trace(go.Bar(
                x=comp_serv["resp"],
                y=comp_serv["prop"],
                text=round(comp_serv["prop"], 1),
                name=servicio,
                marker=dict(color=COLORES_SERVICIO[servicio]),
            ))
        fig_crit.update_xaxes(
            title="Nivel",
        )
        fig_crit.update_yaxes(
            title="Porcentaje",
        )
        fig_crit.update_layout(
            margin=dict(t=20, b=20),
            height=250,
            font=dict(
                family="Noto Sans",
                size=13
                ),
            )
        st.plotly_chart(fig_crit, key=f"comp_fig_{criterio}")
