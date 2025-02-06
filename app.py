import streamlit as st

pages = {
    "Resultados": [
        st.Page("medias.py",  title="Medias"),
        st.Page("conteos.py", title="Conteos"),
        st.Page("items.py",   title="Items"),
    ]
}

pg = st.navigation(pages)
pg.run()