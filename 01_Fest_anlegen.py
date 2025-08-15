import streamlit as st
import os
from datetime import datetime
import pandas as pd
from datenbank import SessionLocal, FestTyp, Fest, Bestellung, Einkauf
from import_tools import importiere_excel_in_bestellungen
from auth import login

if login():
    st.set_page_config(page_title="Fest anlegen", page_icon="🎪")

    st.subheader("🎭 Feste verwalten")

    with st.form("festtyp_anlegen", clear_on_submit=True):
        neuer_festtyp = st.text_input("Neues Fest hinzufügen")
        festtyp_submit = st.form_submit_button("➕ Fest anlegen")
        if festtyp_submit and neuer_festtyp:
            session = SessionLocal()
            if session.query(FestTyp).filter_by(name=neuer_festtyp).first():
                st.warning("Fest existiert bereits.")
            else:
                session.add(FestTyp(name=neuer_festtyp))
                session.commit()
                st.success(f"Fest '{neuer_festtyp}' wurde angelegt.")
            session.close()
            st.rerun()

    st.subheader("📥 Neue Veranstaltung hinzufügen & Bestellungen importieren")

    session = SessionLocal()
    festtypen = session.query(FestTyp).all()
    festtyp_namen = [ft.name for ft in festtypen]

    with st.form("neues_fest", clear_on_submit=True):
        festtyp_auswahl = st.selectbox("🎭 Festtyp auswählen", festtyp_namen)
        fest_datum = st.date_input("📅 Datum des Fests")
        uploaded_file = st.file_uploader("📄 Excel-Datei hochladen", type=["xls", "xlsx"])
        submit = st.form_submit_button("✅ Fest anlegen")

        if submit:
            if not uploaded_file or not festtyp_auswahl:
                st.warning("Bitte Fest und Excel-Datei angeben.")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"uploads/{festtyp_auswahl}_{fest_datum.strftime('%d.%m.%Y')}_{timestamp}.xlsx"
                os.makedirs("uploads", exist_ok=True)
                with open(filename, "wb") as f:
                    f.write(uploaded_file.read())

                festtyp_obj = session.query(FestTyp).filter_by(name=festtyp_auswahl).first()
                neues_fest = Fest(excel_filename=filename, datum=fest_datum, festtyp_id=festtyp_obj.id)
                session.add(neues_fest)
                session.commit()

                anzahl = importiere_excel_in_bestellungen(filename, neues_fest.id)
                st.success(f"✅ Fest *{festtyp_auswahl}* wurde angelegt. {anzahl} Bestellungen importiert.")
                session.close()

    st.divider()
    st.subheader("📋 Bestehende Feste")

    feste = session.query(Fest).order_by(Fest.datum.desc()).all()

    if not feste:
        st.info("Noch keine Feste vorhanden.")
    else:
        for fest in feste:
            with st.container():
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"### 🎪 {fest.festtyp.name}")
                    st.markdown(f"📅 {fest.datum.strftime('%d.%m.%Y')}")
                with col2:
                    delete_key = f"delete_{fest.id}"
                    confirm_key = f"confirm_delete_{fest.id}"
                    if st.button("🗑️", key=delete_key):
                        st.session_state[confirm_key] = True
                    if st.session_state.get(confirm_key, False):
                        st.warning("Möchten Sie dieses Fest wirklich löschen?")
                        if st.button("Ja, löschen", key=f"confirm_yes_{fest.id}"):
                            session.query(Bestellung).filter_by(fest_id=fest.id).delete()
                            session.query(Einkauf).filter_by(fest_id=fest.id).delete()
                            session.delete(fest)
                            session.commit()
                            st.session_state[confirm_key] = False
                            st.rerun()
                        if st.button("Abbrechen", key=f"confirm_no_{fest.id}"):
                            st.session_state[confirm_key] = False
                st.markdown("---")
