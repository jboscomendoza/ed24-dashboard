import pyarrow
import streamlit as st
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from textwrap import wrap

NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
}
COLORES = ["#fcb1c3", "#fce397", "#bae673", "#a4dafc"]
COLORES_RESP = dict(zip(["N0", "N1", "N2", "N3"], COLORES))

COLS_INFORMACION = ["campo", "contenido", "pda", "descriptor", "criterio"]

st.set_page_config(
    page_title="Conteos por criterio - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    #layout="wide",
)

diccionario = pl.read_parquet("data/diccionario.parquet").drop(["fase", "nivel", "grado"])
rubrica = pl.read_parquet("data/diccionario_rubrica.parquet")

conteo = pl.read_parquet("data/item_conteo_grado.parquet")
conteo = conteo.join(diccionario, how="inner", on="item").join(
    rubrica, how="inner", on=["item", "resp"]
).with_columns(
    pl.col(["consigna", "grado"]).cast(pl.Int16).cast(pl.String)
)

nivel_0 = (
    conteo.filter(pl.col("resp") == "N0")
    .select(["item", "grado", "prop"])
    .rename({"prop": "nivel_0"})
)
nivel_3 = (
    conteo.filter(pl.col("resp") == "N3")
    .select(["item", "grado", "prop"])
    .rename({"prop": "nivel_3"})
)
conteo_grado = conteo.join(nivel_0, on=["item", "grado"], how="left").join(
    nivel_3, on=["item", "grado"], how="left"
)

#### Streamlit ####

eias = conteo["eia"].unique(maintain_order=True)
sel_eia = st.selectbox("EIA", options=eias)
conteo_filtro = conteo.filter(pl.col("eia") == sel_eia)

procesos = conteo_filtro["proceso"].unique(maintain_order=True)
sel_proceso = st.multiselect("Habilidad", options=procesos, default=procesos)
conteo_filtro = conteo_filtro.filter(pl.col("proceso").is_in(sel_proceso))

st.title(f"{sel_eia}")
for proceso in sel_proceso:
    conteo_proceso = conteo_filtro.filter(pl.col("proceso") == proceso)
    st.markdown(f"## {proceso}")

    criterios = conteo_proceso["criterio"].unique()
    num_criterios = len(criterios)
    nom_criterios = [i[0:70] + "..." if len(i) > 70 else i for i in criterios]
    nom_criterios = ["<br>".join(wrap(i, 20)) for i in nom_criterios]

    figura = make_subplots(
        rows=1,
        cols=num_criterios,
        subplot_titles=nom_criterios,
        x_title="Grado",
        y_title="Porcentaje",
        shared_xaxes=True,
        shared_yaxes=True,
    )
    for id_criterio in range(num_criterios):
        criterio = criterios[id_criterio]
        conteo_criterio = conteo_proceso.filter(pl.col("criterio") == criterio)

        for resp in conteo_criterio["resp"].unique(maintain_order=True):
            conteo_resp = conteo_criterio.filter(pl.col("resp") == resp)
            figura.add_trace(
                go.Bar(
                    x=conteo_resp["grado"],
                    y=conteo_resp["prop"],
                    name=resp,
                    legendgroup="group",
                    text=conteo_resp["prop"].round(1),
                    hovertext=conteo_resp["campo"],
                    insidetextanchor="middle",
                    marker=dict(
                        color=COLORES_RESP[resp],
                    ),
                ),
                row=1,
                col=id_criterio + 1,
            )
            if id_criterio != num_criterios - 1:
                figura.update_traces(
                    showlegend=False,
                )
    figura.update_xaxes(
        title="",
        type="category",
    )
    figura.update_yaxes(
        title="",
    )
    figura.update_annotations(
        font_size=13,
        font_family="Noto Sans Condensed, sans",
    )
    figura.update_layout(
        barmode="stack",
        height=425,
        width=180 * num_criterios,
        margin=dict(b=30),
        font=dict(family="Noto Sans", size=13),
    )
    st.plotly_chart(figura, use_container_width=False)

    if st.checkbox("Mostrar información del proceso.", key=f"check_info_{proceso}"):
        st.markdown("### Información del proceso")
        sel_cols = st.multiselect(
            "Columnas para mostrar:",
            options=COLS_INFORMACION,
            default=COLS_INFORMACION,
            key=f"multiselect_{id_criterio}{proceso}"
        )
        st.table(
            (
                conteo_proceso[sel_cols]
                .rename(str.title)
                .unique(maintain_order=True)
                .to_pandas()
                .set_index("Campo")
            )
        )

    if st.checkbox("Mostrar niveles de la rúbrica.", key=f"check_rubrica_{id_criterio}{proceso}"):
        st.markdown("### Niveles de la rúbrica")
        sel_criterios = st.selectbox("Criterio", options=criterios, index=0)
        conteo_criterio = (
            conteo_proceso
            .filter(pl.col("criterio") == sel_criterios, pl.col("resp") != "N0")
            .unique(maintain_order=True)
            .select(["criterio", "resp", "resp_nivel", "resp_rubrica"])
            .rename(
                {
                    "criterio": "Criterio",
                    "resp": "Nivel",
                    "resp_nivel": "Descripcion",
                    "resp_rubrica": "Rúbrica",
                }
            )
            .to_pandas()
            .set_index("Criterio")
        )
        st.table(conteo_criterio)
