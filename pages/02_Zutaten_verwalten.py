import streamlit as st
from datenbank import SessionLocal, Zutat
from auth import login

if login():
    st.set_page_config(page_title="Zutaten verwalten", page_icon="🧂")
    st.subheader("🧂 Zutaten verwalten")

    session = SessionLocal()

    # Neue Zutat hinzufügen
    with st.form("zutat_formular"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name der Zutat", placeholder="z. B. Grillwurst")
        with col2:
            einheit = st.selectbox("Einheit", ["kg", "l", "Stück"])

        speichern = st.form_submit_button("➕ Zutat hinzufügen")

        if speichern and name:
            # Prüfen ob Zutat schon existiert
            vorhandene = session.query(Zutat).filter(Zutat.name == name).first()
            if vorhandene:
                st.warning("Diese Zutat existiert bereits.")
            else:
                neue_zutat = Zutat(name=name.strip(), einheit=einheit)
                session.add(neue_zutat)
                session.commit()
                st.success(f"Zutat „{name}“ wurde gespeichert!")
                st.rerun()

    st.markdown("---")

    # Vorhandene Zutaten anzeigen
    zutaten = session.query(Zutat).order_by(Zutat.name).all()

    if not zutaten:
        st.info("Noch keine Zutaten angelegt.")
    else:
        st.markdown("### 🗃️ Vorhandene Zutaten")
        for zutat in zutaten:
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"**{zutat.name}**")
            with col2:
                st.markdown(f"{zutat.einheit}")
            with col3:
                if st.button("🗑️", key=f"delete_zutat_{zutat.id}"):
                    session.delete(zutat)
                    session.commit()
                    st.rerun()

    session.close()
