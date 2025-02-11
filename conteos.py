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

conteo_servicio = pd.read_parquet("data/item_conteo_servicio.parquet")
conteo_servicio = conteo_servicio.merge(diccionario, how="inner", on="item")
nivel_0_servicio = (
    conteo_servicio
    .loc[conteo_servicio["resp"] == "N0"][["item", "grado", "servicio", "prop"]]
    .rename(columns={"prop":"nivel_0"})
    )
nivel_3_servicio = (
    conteo_servicio
    .loc[conteo_servicio["resp"] == "N3"][["item", "grado", "servicio", "prop"]]
    .rename(columns={"prop":"nivel_3"})
    )
conteo_servicio = (
    conteo_servicio
    .merge(nivel_0_servicio, on=["item", "grado", "servicio"], how="left")
    .merge(nivel_3_servicio, on=["item", "grado", "servicio"], how="left")
    )


procesos = conteo_grado["proceso"].unique()

#### Streamlit ####

st.set_page_config(
    page_title="Conteos - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

st.title("Conteos Evaluación Diagnóstica 2024")

tab_grado, tab_servicios = st.tabs(["Grado", "Servicios"])

with tab_grado:
    with st.sidebar:
        sel_cnt_nivel = st.selectbox("Nivel", options = NIVELES_GRADO.keys(), index=2)
        sel_cnt_grado = st.selectbox("Grado", options = NIVELES_GRADO[sel_cnt_nivel])

    conteo_grado_filtro = conteo_grado.loc[
        (conteo_grado["nivel"] == sel_cnt_nivel) &
        (conteo_grado["grado"] == sel_cnt_grado)
    ].sort_values(["proceso", "consigna", "inciso", "criterio_num"])

    eia_filtro = conteo_grado_filtro["eia"].unique()

    with st.sidebar:
        sel_cnt_eia = st.multiselect("EIA", options=eia_filtro, default=eia_filtro)
        sel_cnt_proceso = st.multiselect("Proceso", options = procesos, default=procesos)

    conteo_grado_filtro = conteo_grado_filtro.loc[
        (conteo_grado_filtro["eia"].isin(sel_cnt_eia)) &
        (conteo_grado_filtro["proceso"].isin(sel_cnt_proceso))
    ]

    orden = st.radio(
        "Ordenar por:",
        ["Reactivo", "Campo", "Nivel 0", "Nivel 3"],
        horizontal=True
        )

    for eia in conteo_grado_filtro["eia"].unique():
        st.markdown(f"### {eia}")
        conteo_eia = conteo_grado_filtro.loc[conteo_grado_filtro["eia"] == eia]

        if orden == "Reactivo":
            conteo_eia = conteo_eia.sort_values(["consigna", "inciso", "item"])
        elif orden == "Campo":
            conteo_eia = conteo_eia.sort_values(["campo", "item"])
        elif orden == "Nivel 0":
            conteo_eia = conteo_eia.sort_values(["nivel_0", "item"])
        elif orden == "Nivel 3":
            conteo_eia = conteo_eia.sort_values(["nivel_3", "item"])
        
        fig = px.bar(
            conteo_eia,
            x="item",
            y="prop",
            color="resp",
            text=conteo_eia["prop"].round(),
            color_discrete_sequence=COLORES,
            hover_name="proceso",
            hover_data=["eia", "descriptor", "criterio", "campo"],
            labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"},
            height=350,
        )
        fog = px.line(
            conteo_eia,
            x="item",
            y="prop",
            color="resp",
            markers=True,
            color_discrete_sequence=COLORES,
            hover_name="proceso",
            hover_data=["eia", "descriptor", "criterio", "campo"],
            labels={"prop":"Porcentaje", "item":"Criterio", "resp":"Respuesta"},
            height=350,
        )
        st.plotly_chart(fig)
        st.plotly_chart(fog)

with tab_servicios:
    servicios = conteo_servicio["servicio"].unique()
    sel_servicio = st.multiselect("Tipo de servicio", options=servicios, default=servicios)

    conteo_servicio_filtro = conteo_servicio.loc[
        (conteo_servicio["nivel"] == sel_cnt_nivel) &
        (conteo_servicio["grado"] == sel_cnt_grado) &
        (conteo_servicio["servicio"].isin(sel_servicio))
        ]
    
    orden_servicio = st.radio(
        "Ordenar por:",
        ["Reactivo", "Campo", "Nivel 0", "Nivel 3"],
        horizontal=True, 
        key="orden_servicio"
        )

    for servicio in conteo_servicio_filtro["servicio"].unique():
        st.markdown(f"### {servicio}")
        conteo_serv = conteo_servicio_filtro.loc[conteo_servicio_filtro["servicio"] == servicio]
        
        if orden_servicio == "Reactivo":
            conteo_serv = conteo_serv.sort_values(["consigna", "inciso", "item"])
        elif orden_servicio == "Campo":
            conteo_serv = conteo_serv.sort_values(["campo", "item"])
        elif orden_servicio == "Nivel 0":
            conteo_serv = conteo_serv.sort_values(["nivel_0", "item"])
        elif orden_servicio == "Nivel 3":
            conteo_serv = conteo_serv.sort_values(["nivel_3", "item"])
        
        plotino = go.Figure()
        for resp in conteo_serv["resp"].unique():
            conteo_resp = conteo_serv.loc[conteo_serv["resp"] == resp]
            plotino.add_trace(go.Bar(
                x=conteo_resp["item"],
                y=conteo_resp["prop"],
                name=resp, 
                text=round(conteo_resp["prop"]),
                marker=dict(color=COLORES_RESP[resp]),
                ))
        plotino.update_layout(
            barmode="relative", 
            height=350,
            margin=dict(t=45),
            )
        st.plotly_chart(plotino)
    st.dataframe(
        conteo_servicio_filtro[["item", "campo", "pda", "descriptor", "criterio"]].drop_duplicates(),
        height=350,
        )