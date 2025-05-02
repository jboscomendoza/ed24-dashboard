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
COLORES_CAMPO = {
    "LEN": "#c00000",
    "SPC": "#0070c0",
    "ENS": "#00b050",
    "HYC": "#7030a0",
}
CLAVE_RESP = ["N0", "N1", "N2", "N3"]
DESC_RESP = [
    "Sin evidencias de desarrollo del aprendizaje",
    "Requiere apoyo para desarrollar el aprendizaje",
    "En proceso de desarrollo",
    "Aprendizaje desarrollado",
]
# DESC_RESP = ["<br>".join(wrap(i, width=16)) for i in DESC_RESP]
CLAVE_DICT = dict(zip(CLAVE_RESP, DESC_RESP))
CLAVE_SERV = ["Nacional", "General", "Privada", "Técnica", "Telesecundaria"]
COLORES_RESP = dict(zip(DESC_RESP, COLORES))
COLORES_SERVICIO = dict(
    zip(
        CLAVE_SERV,
        ["#ffadad", "#fcf6bd", "#d0f4de", "#a9def9", "#e4c1f9"],
    )
)
PROCESOS = [
    "Comprensión",
    "Utilización del conocimiento",
    "Propuesta de solución",
    "Juicio crítico",
]
COLS_INFORMACION = ["campo", "contenido", "pda", "descriptor", "criterio_titulo"]
RUTA_DICT = "data/diccionario.parquet"
RUTA_RUBR = "data/diccionario_rubrica.parquet"
RUTA_CONT = "data/item_conteo_ponderado.parquet"

st.set_page_config(
    page_title="Conteos por criterio - Evaluación diagnóstica 2024",
    page_icon=":worm:",
    layout="wide",
)


@st.cache_data
def crear_conteo(ruta_dict, ruta_rubr, ruta_cont):
    diccionario = pl.read_parquet(ruta_dict).drop(["fase", "nivel", "grado"])
    rubrica = pl.read_parquet(ruta_rubr)
    conteo_ponderado = pl.read_parquet(ruta_cont)
    conteo = (
        conteo_ponderado.join(diccionario, on="item", how="inner")
        .join(rubrica, on=["item", "resp"], how="inner")
        .unique()
    )
    conteo = conteo.with_columns(
        pl.col("resp").replace(CLAVE_DICT).cast(pl.Enum(DESC_RESP)),
        pl.col("servicio").cast(pl.Enum(CLAVE_SERV)),
        pl.col("consigna").cast(pl.Int16).cast(pl.String),
    ).sort(["eia_clave", "grado", "proceso", "resp"])
    # Agrega HTML de color para los nombres de campo de cada criterio
    conteo = conteo.with_columns(
        pl.Series(
            name="campo_color",
            values=[
                f'<span style="color:{COLORES_CAMPO[i]};">{i}</span><br>'
                for i in conteo["campo_clave"]
            ],
        ),
        criterio_titulo=conteo["criterio"],
    )
    conteo = conteo.with_columns(criterio=conteo["campo_color"] + conteo["criterio"])
    return conteo


conteo = crear_conteo(RUTA_DICT, RUTA_RUBR, RUTA_CONT)

#### Streamlit ####
with st.sidebar:
    st.markdown("### Únicamente fase 6")
    servicios = conteo.sort("servicio")["servicio"].unique(maintain_order=True).to_list()
    eias = conteo.sort(["eia_clave"])["eia"].unique(maintain_order=True).to_list()
    sel_servicio = st.selectbox("Servicio", options=servicios, index=0)
    sel_eia = st.selectbox("EIA", options=eias, index=0)
    conteo_filtro = conteo.filter(
        pl.col("servicio") == sel_servicio, pl.col("eia") == sel_eia
    )

st.title(f"{sel_eia}")

tab_graficas, tab_tablas, tab_espec, tab_comparativos = st.tabs(
    ["Gráficas", "Tablas", "Especificaciones", "Comparativos"]
)

with tab_graficas:
    for proceso in PROCESOS:
        conteo_proceso = conteo_filtro.filter(pl.col("proceso") == proceso).sort(["criterio_clave"])
        if not conteo_proceso.is_empty():
            st.markdown(f"## {proceso}")
            # Numero de grados para definir el ancho de los graficos
            num_grados = len(conteo_proceso["grado"].unique(maintain_order=True).to_list())
            criterios = conteo_proceso["criterio"].unique(maintain_order=True).to_list()
            
            # Divide HTML de color y texto del criterio
            html_criterios = [i.split("<br>")[0] for i in criterios]
            texto_criterios = [i.split("<br>")[1] for i in criterios]
            num_criterios = len(criterios)
            # Texto del criterio truncado a tres renglones
            if num_grados > 1:
                ancho_col = 70
                ancho_lab = 24
            else:
                ancho_col = 80
                ancho_lab = 18
            ancho_plot = (ancho_col * num_grados * num_criterios) + 70
            texto_criterios = [
                "<br>".join(wrap(i, width=ancho_lab, max_lines=3, placeholder="..."))
                for i in texto_criterios
            ]
            # HTML + Texto para mostrar con color
            nom_criterios = [
                f"{i}<br>{j}" for i, j in zip(html_criterios, texto_criterios)
            ]
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
                for resp in conteo_criterio["resp"].unique(maintain_order=True).to_list():
                    conteo_resp = conteo_criterio.filter(pl.col("resp") == resp)
                    figura.add_trace(
                        go.Bar(
                            x=conteo_resp["grado"],
                            y=conteo_resp["prop"],
                            name=resp,
                            showlegend=False,
                            text=conteo_resp["prop"].round(1).to_list(),
                            hovertext=conteo_resp["campo"]
                            + "<br>Consigna "
                            + conteo_resp["consigna"]
                            + "<br>Inciso "
                            + conteo_resp["inciso"],
                            insidetextanchor="middle",
                            marker=dict(
                                color=COLORES_RESP[resp],
                            ),
                        ),
                        row=1,
                        col=id_criterio + 1,
                    )
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
                margin=dict(t=70, b=25, r=15),
                font=dict(family="Noto Sans Condensed", size=12),
                legend_font_size=11,
                legend_font_family="Noto Sans Condensed",
                legend=dict(
                    yref="container",
                    y=1.1,
                    orientation="h",
                ),
            )
            st.plotly_chart(figura, use_container_width=False)

with tab_tablas:
    for proceso in PROCESOS:
        tabla_prop = conteo_filtro.filter(pl.col("proceso") == proceso)
        if not tabla_prop.is_empty():
            st.markdown(f"## {proceso}")
            tabla_prop = (
                tabla_prop
                .with_columns(pl.col("prop").round(1).cast(pl.Decimal(scale=1)))
                .pivot(
                    "resp",
                    index=["criterio_clave", "criterio_titulo", "grado"],
                    values="prop",
                    aggregate_function="first",
                )
                .sort(["criterio_clave", "grado"])
                .rename({"criterio_titulo":"criterio"})
                .drop("criterio_clave")
                .rename(str.capitalize)
            )
            # to_pandas para ocultar columna index
            st.table(tabla_prop.to_pandas().set_index("Criterio"))
            

with tab_espec:
    for proceso in PROCESOS:
        tabla_proceso = conteo_filtro.filter(pl.col("proceso") == proceso)
        if not tabla_proceso.is_empty():
            st.markdown(f"## {proceso}")
            st.markdown("### Contenidos")
            st.table(
                (
                    tabla_proceso.select(pl.col(COLS_INFORMACION))
                    .unique()
                    .sort(["campo", "criterio_titulo"])
                    .rename({"criterio_titulo":"criterio"})
                    .rename(str.capitalize)
                )
            )
            st.markdown("### Niveles de la rúbrica")
            criterios_titulo = tabla_proceso["criterio_titulo"].unique(maintain_order=True).to_list()
            sel_criterios = st.selectbox("Criterio", options=criterios_titulo, index=0)
            tabla_criterio = (
                tabla_proceso.filter(
                    pl.col("criterio_titulo") == sel_criterios,
                    pl.col("resp") != "Sin evidencias de desarrollo del aprendizaje",
                )
                .select(pl.col(["consigna", "inciso", "resp", "resp_rubrica"]))
                .unique()
                .sort("resp")
                .rename(
                    {
                        "consigna": "Consigna",
                        "inciso": "Inciso",
                        "resp": "Nivel",
                        "resp_rubrica": "Rúbrica",
                    }
                )
            )
            st.table(tabla_criterio)

with tab_comparativos:
    comp = conteo.filter(pl.col("eia") == sel_eia)
    comp = comp.with_columns(
        pl.Series(
            name="resp", values=["<br>".join(wrap(i, width=16)) for i in comp["resp"]]
        )
    )
    criterios_comp = comp["criterio"].unique().to_list()
    grados_comp = comp["grado"].unique().to_list()
    criterios_comp.sort()
    grados_comp.sort()
    st.markdown("## Comparativos")
    sel_grado = st.selectbox("Grado", options=grados_comp)
    for criterio in criterios_comp:
        st.markdown(f"### {criterio}", unsafe_allow_html=True)
        comp_criterio = comp.filter(
            (pl.col("criterio") == criterio) & (pl.col("grado") == sel_grado)
        )
        fig_crit = go.Figure()
        for servicio in servicios:
            comp_serv = comp_criterio.filter(pl.col("servicio") == servicio)
            fig_crit.add_trace(
                go.Bar(
                    x=comp_serv["resp"],
                    y=comp_serv["prop"],
                    text=comp_serv["prop"].round(1).to_list(),
                    name=servicio,
                    marker=dict(color=COLORES_SERVICIO[servicio]),
                )
            )
        fig_crit.update_xaxes(
            title="Nivel",
        )
        fig_crit.update_yaxes(
            title="Porcentaje",
        )
        fig_crit.update_layout(
            margin=dict(t=20, b=20),
            height=250,
            font=dict(family="Noto Sans", size=13),
        )
        st.plotly_chart(fig_crit, key=f"comp_fig_{criterio}")
