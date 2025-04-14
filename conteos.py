import pyarrow
import streamlit as st
import pandas as pd
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
COLORES_PROCESO = dict(
    zip(
        [
            "Recuperación de información",
            "Comprensión",
            "Análisis",
            "Utilización del conocimiento",
            "No definido",
        ],
        ["#8338ec", "#ffca3a", "#8ac926", "#1982c4", "#cccccc"],
    )
)

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

conteo = read_conteo("data/st_conteo.parquet")

# Elementos unicos
procesos = conteo["proceso"].unique()
campos = conteo["campo"].unique()

st.title("Conteos Evaluación Diagnóstica 2024")

with st.sidebar:
    sel_nivel = st.selectbox("Nivel", options=NIVELES_GRADO.keys(), index=2)
    sel_grado = st.selectbox("Grado", options=NIVELES_GRADO[sel_nivel], index=0)

conteo_filtro = conteo.filter(
    pl.col("nivel") == sel_nivel,
    pl.col("grado") == sel_grado
).sort(["proceso", "consigna", "inciso", "criterio_num"])

eia_filtro = conteo_filtro["eia"].unique()

with st.sidebar:
    sel_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
    sel_proceso = st.multiselect("Proceso", options=procesos, default=procesos)
    sel_campo = st.multiselect("Campo formativo", options=campos, default=campos)

conteo_filtro = conteo_filtro.filter(
    pl.col("eia").is_in(sel_eia),
    pl.col("proceso").is_in(sel_proceso),
    pl.col("campo").is_in(sel_campo)
)

st.markdown("**Ordenar por:**")
sel_orden = st.radio(
    "Ordenar por:",
    ["Reactivo", "Proceso", "Campo", "Nivel 0", "Nivel 3"],
    horizontal=True,
    label_visibility="collapsed",
)

for eia in conteo_filtro["eia"].unique():
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
    conteo_media = conteo_eia.select(pl.col(["item", "media", "proceso"])).unique()
    plot_medias.add_trace(
        go.Scatter(
            x=conteo_media["item"],
            y=conteo_media["media"],
            name="Media",
            mode="lines+markers+text",
            text=conteo_media["media"].round(2),
            hovertext=conteo_media["proceso"],
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
        conteo_irt = (
            conteo_eia
            .filter(pl.col("resp") == resp)
            .select(pl.col(["item", "dificultad", "resp"]))
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
        conteo_eia_resp = (
            conteo_eia
            .filter(pl.col("resp") == resp)
            .select(pl.col(["resp", "item", "prop"]))
            )
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
        st.table(
            (
                conteo_eia[
                    [
                        "item",
                        "proceso",
                        "campo",
                        "contenido",
                        "pda",
                        "descriptor",
                        "criterio",
                    ]
                ]
                .drop_duplicates()
                .reset_index(drop=True)
            )
        )

# tab_grado, tab_servicios = st.tabs(["Grado", "Servicios"])
# Conteo por servicio
# conteo_servicio = pd.read_parquet("data/item_conteo_servicio.parquet")
# conteo_servicio = conteo_servicio.merge(diccionario, how="inner", on="item")
# nivel_0_servicio = (
#     conteo_servicio
#     .loc[conteo_servicio["resp"] == "N0"][["item", "grado", "servicio", "prop"]]
#     .rename(columns={"prop":"nivel_0"})
#     )
# nivel_3_servicio = (
#     conteo_servicio
#     .loc[conteo_servicio["resp"] == "N3"][["item", "grado", "servicio", "prop"]]
#     .rename(columns={"prop":"nivel_3"})
#     )
# conteo_servicio = (
#     conteo_servicio
#     .merge(nivel_0_servicio, on=["item", "grado", "servicio"], how="left")
#     .merge(nivel_3_servicio, on=["item", "grado", "servicio"], how="left")
#     )
# with tab_servicios:
#     servicios = conteo_servicio["servicio"].unique()
#     sel_servicio = st.multiselect("Tipo de servicio", options=servicios, default=servicios)
#
#     conteo_servicio_filtro = conteo_servicio.loc[
#         (conteo_servicio["nivel"] == sel_nivel) &
#         (conteo_servicio["grado"] == sel_grado) &
#         (conteo_servicio["servicio"].isin(sel_servicio))
#         ]
#
#     orden_servicio = st.radio(
#         "Ordenar por:",
#         ["Reactivo", "Campo", "Nivel 0", "Nivel 3"],
#         horizontal=True,
#         key="orden_servicio"
#         )
#
#     for servicio in conteo_servicio_filtro["servicio"].unique():
#         st.markdown(f"### {servicio}")
#         conteo_serv = conteo_servicio_filtro.loc[conteo_servicio_filtro["servicio"] == servicio]
#
#         if orden_servicio == "Reactivo":
#             conteo_serv = conteo_serv.sort_values(["consigna", "inciso", "item"])
#         elif orden_servicio == "Campo":
#             conteo_serv = conteo_serv.sort_values(["campo", "item"])
#         elif orden_servicio == "Nivel 0":
#             conteo_serv = conteo_serv.sort_values(["nivel_0", "item"])
#         elif orden_servicio == "Nivel 3":
#             conteo_serv = conteo_serv.sort_values(["nivel_3", "item"])
#
#         plotino = go.Figure()
#         for resp in conteo_serv["resp"].unique():
#             conteo_resp = conteo_serv.loc[conteo_serv["resp"] == resp]
#             plotino.add_trace(go.Bar(
#                 x=conteo_resp["item"],
#                 y=conteo_resp["prop"],
#                 name=resp,
#                 text=round(conteo_resp["prop"]),
#                 marker=dict(color=COLORES_RESP[resp]),
#                 ))
#         plotino.update_layout(
#             barmode="relative",
#             height=350,
#             margin=dict(t=45),
#             )
#         st.plotly_chart(plotino)
#     st.dataframe(
#         conteo_servicio_filtro[["item", "campo", "pda", "descriptor", "criterio"]].drop_duplicates(),
#         height=350,
#         )
