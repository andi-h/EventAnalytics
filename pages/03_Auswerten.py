import streamlit as st
from streamlit_option_menu import option_menu
from auth import login

if login():
    # Setze Layout
    st.set_page_config(page_title="Fest Auswertung", layout="wide", page_icon="🎉")

    st.title("🎉 Fest Auswertung")

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
        zutaten_zuordnen.show()

    elif selected == "Einkäufe erfassen":
        from auswertung import einkaeufe
        einkaeufe.show()

    elif selected == "Auswertung":
        from auswertung import analyse
        analyse.show()

    elif selected == "Fest-Vergleich":
        from auswertung import vergleich
        vergleich.show()
