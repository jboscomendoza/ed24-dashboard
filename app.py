import streamlit as st

pages = {
    "Resultados": [
        st.Page("conteos.py", title="Conteos"),
        st.Page("conteos_items.py", title="Conteos por criterio"),
        st.Page("medias.py",  title="Medias"),
        st.Page("irt.py",     title="IRT"),
        st.Page("pefiles.py", title="Perfiles"),
        #st.Page("items.py",   title="Items"),
    ]
}

pg = st.navigation(pages)
pg.run()