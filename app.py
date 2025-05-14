import streamlit as st

pages = {
    "Resultados": [
        st.Page("conteos.py", title="Conteos"),
        st.Page("conteos_items.py", title="Conteos por criterio"),
        #st.Page("conteos_procesos.py", title="Conteos por proceso"),
        st.Page("conteos_no_ponderados.py", title="Conteos no ponderados"),
        st.Page("conteos_ponderados_polars.py", title="Conteos ponderados"),
        st.Page("medias.py",  title="Medias"),
        st.Page("irt.py",     title="IRT"),
        st.Page("perfiles.py", title="Perfiles"),
        st.Page("perfiles_uni.py", title="Perfiles unidimensional"),
        #st.Page("items.py",   title="Items"),
    ]
}

pg = st.navigation(pages)
pg.run()
