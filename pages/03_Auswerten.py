import streamlit as st
from streamlit_option_menu import option_menu
from datenbank import SessionLocal, Fest
from auth import login

if login():
    # Setze Layout
    st.set_page_config(page_title="Fest Auswertung", layout="wide", page_icon="🎉")

    st.title("🎉 Fest Auswertung")

    session = SessionLocal()

    # Fest auswählen
    feste = session.query(Fest).order_by(Fest.datum.desc()).all()
    fest_namen = [f"{fest.festtyp.name} ({fest.datum.strftime('%d.%m.%Y')})" for fest in feste]
    
    col1, col2 = st.columns(2)
    with col1:
        fest_index = st.selectbox("Fest auswählen", options=range(len(feste)), format_func=lambda i: fest_namen[i])
    with col2:
        pass

    aktuelles_fest = feste[fest_index]

    st.divider()

    # Horizontales Menü oben
    selected = option_menu(
        menu_title=None,
        options=[
            "Zutaten zuordnen",
            "Einkäufe erfassen",
            "Auswertung",
            "Fest-Vergleich"
        ],
        icons=["file-plus", "clipboard-check", "cart", "bar-chart-line", "calendar-range"],
        orientation="horizontal"
    )

    # Seiteninhalt laden
    if selected == "Zutaten zuordnen":
        from auswertung import zutaten_zuordnen
        zutaten_zuordnen.show(session, feste, aktuelles_fest)

    elif selected == "Einkäufe erfassen":
        from auswertung import einkaeufe
        einkaeufe.show(session, feste, aktuelles_fest)

    elif selected == "Auswertung":
        from auswertung import analyse
        analyse.show(session, feste, aktuelles_fest)

    elif selected == "Fest-Vergleich":
        from auswertung import vergleich
        vergleich.show(session, feste, aktuelles_fest)
