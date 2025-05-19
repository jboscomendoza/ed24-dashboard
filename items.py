import streamlit as st
import polars as pl
import plotly.express as px


NIVELES_GRADO = {
    "Preescolar": [3],
    "Primaria": [1, 2, 3, 4, 5, 6],
    "Secundaria": [1, 2, 3],
}
RUTA_ITEMS = "data/ed24-items.parquet"


st.set_page_config(
    page_title="Evaluación diagnóstica 2024 - Items",
    page_icon=":worm:",
    layout="wide",
)


@st.cache_data
def importar_items(ruta: str) -> pl.DataFrame:
    """Lee los datos de items desde parquet a un dataframe de polars."""
    data_items = pl.read_parquet(ruta)
    return data_items


#### Streamlit #####
st.title("Evaluación Diagnóstica 2024")

ed24 = importar_items(RUTA_ITEMS)

with st.sidebar:
    select_nivel = st.selectbox("Nivel", options=NIVELES_GRADO.keys())
    select_grado = st.selectbox("Grado", options=NIVELES_GRADO[select_nivel])

ed_filtro = ed24.filter(
    pl.col("nivel") == select_nivel,
    pl.col("grado") == select_grado,
)

eia_filtro = ed_filtro["eia"].unique(maintain_order=True)
campo_filtro = ed_filtro["campo"].unique(maintain_order=True)

with st.sidebar:
    select_eia = st.multiselect("EIA", eia_filtro, default=eia_filtro)
    select_campo = st.multiselect("Campo formativo", campo_filtro, default=campo_filtro)

ed_filtro = (
    ed_filtro.filter(
        pl.col("eia").is_in(select_eia),
        pl.col("campo").is_in(select_campo),
    )
    .rename(str.capitalize)
    .rename({"Item_nivel": "Item nivel"})
)

st.markdown("## Dificultad de los criterios")

fig = px.scatter(
    ed_filtro,
    x="Item",
    y="Dificultad",
    color="Item nivel",
    hover_data=["Eia", "Descriptor", "Criterio"],
    color_discrete_sequence=["#f94144", "#f9c74f", "#43aa8b"],
    hover_name="Campo",
    range_y=[0, 800],
)

st.plotly_chart(fig)

st.markdown("## Contenido de los EIA")
for i in eia_filtro:
    st.markdown(f"### {i}")
    st.table(
        (
            ed_filtro.filter(pl.col("Eia") == i)
            .select(pl.col(["Item", "Campo", "Pda", "Descriptor", "Criterio"]))
            .unique(maintain_order=True)
            .to_pandas()
            .set_index("Item")
        )
    )