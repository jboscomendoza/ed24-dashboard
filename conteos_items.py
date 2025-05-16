import pyarrow
import streamlit as st
import polars as pl
import plotly.graph_objects as go

COLORES = ["#fcb1c3", "#fce397", "#bae673", "#a4dafc"]
COLORES_RESP = dict(zip(["N0", "N1", "N2", "N3"], COLORES))

COLS_INFORMACION = ["campo", "contenido", "pda", "descriptor", "proceso"]

st.set_page_config(
    page_title="Conteos por criterio - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)

diccionario = pl.read_parquet("data/diccionario.parquet").drop(["fase", "nivel", "grado"])
rubrica = pl.read_parquet("data/diccionario_rubrica.parquet")
conteo = pl.read_parquet("data/item_conteo_grado.parquet")
conteo = conteo.join(diccionario, how="inner", on="item").join(rubrica, how="inner", on=["item", "resp"])

conteo = conteo.with_columns(
    pl.col(["consigna", "grado"]).cast(pl.Int16).cast(pl.String)
)

nivel_0 = conteo.filter(pl.col("resp") == "N0").select(
    ["item", "grado", "prop"]).rename({"prop": "nivel_0"})
nivel_3 = conteo.filter(pl.col("resp") == "N3").select(
    ["item", "grado", "prop"]).rename({"prop": "nivel_3"})
conteo = conteo.join(nivel_0, on=["item", "grado"], how="left").join(
    nivel_3, on=["item", "grado"], how="left"
)

#### Streamlit ####
eias = conteo["eia"].unique(maintain_order=True)
sel_eia = st.selectbox("EIA", options=eias)
conteo_filtro = conteo.filter(pl.col("eia") == sel_eia)
consignas = conteo_filtro["consigna"].unique().sort()
sel_consigna = st.selectbox("Consigna", options=consignas)
conteo_filtro = conteo_filtro.filter(pl.col("consigna") == sel_consigna)

st.markdown(f"# {conteo_filtro['eia'].unique()[0]} (Consigna {sel_consigna})")

criterios = conteo_filtro["criterio"].unique()
sel_criterios = st.multiselect("Criterios", options=criterios, default=criterios)
conteo_filtro = conteo_filtro.filter(pl.col("criterio").is_in(sel_criterios))

for criterio in sel_criterios:
    st.divider()
    st.markdown(f"## {criterio}")
    conteo_criterio = conteo_filtro.filter(pl.col("criterio") == criterio)
    figura = go.Figure()
    for resp in conteo_criterio["resp"].unique(maintain_order=True):
        conteo_resp = conteo_criterio.filter(pl.col("resp") == resp)
        figura.add_trace(
            go.Bar(
                y=conteo_resp["grado"],
                x=conteo_resp["prop"],
                name=resp,
                text=conteo_resp["prop"].round(1),
                insidetextanchor="middle",
                marker=dict(color=COLORES_RESP[resp]),
                orientation="h",
            )
        )
    figura.update_layout(
        barmode="stack",
        height=225,
        width=600,
        margin=dict(t=30, b=30),
        yaxis=dict(
            title="Grado",
            tickmode="array",
            tickvals=conteo_criterio["grado"],
            ticktext=conteo_criterio["grado"].unique(maintain_order=True),
            autorange="reversed",
        ),
        xaxis=dict(title="Porcentaje"),
        font=dict(family="Noto Sans, serif", size=16),
    )
    st.plotly_chart(figura)

    st.markdown("### Información del criterio")
    st.table(
        (
            conteo_criterio[COLS_INFORMACION]
            .rename(str.title)
            .unique(maintain_order=True).to_pandas().set_index("Campo")
        )
    )
    conteo_criterio = (
        conteo_criterio[["resp", "resp_nivel", "resp_rubrica"]]
        .unique(maintain_order=True)
        .rename(
            {
                "resp": "Respuesta",
                "resp_nivel": "Nivel",
                "resp_rubrica": "Rúbrica",
            }
        )
        .to_pandas()
        .set_index("Respuesta")
    )
    st.markdown("### Niveles de la rúbrica")
    st.table(conteo_criterio)