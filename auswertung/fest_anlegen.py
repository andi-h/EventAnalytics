import streamlit as st
import os
from datetime import datetime
import pandas as pd
from datenbank import SessionLocal, Fest, Bestellung, Einkauf
from import_tools import importiere_excel_in_bestellungen

def show():
    st.subheader("📥 Neues Fest anlegen & Bestellungen importieren")

    with st.form("neues_fest", clear_on_submit=True):
        fest_name = st.text_input("🎪 Name des Fests", placeholder="z. B. 1. Konviktgartenkonzert")
        fest_datum = st.date_input("📅 Datum des Fests")
        uploaded_file = st.file_uploader("📄 Excel-Datei hochladen", type=["xls", "xlsx"])
        submit = st.form_submit_button("✅ Fest anlegen")

        if submit:
            if not fest_name or not uploaded_file:
                st.warning("Bitte Festnamen und Excel-Datei angeben.")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"uploads/{fest_name}_{timestamp}.xlsx"
                os.makedirs("uploads", exist_ok=True)
                with open(filename, "wb") as f:
                    f.write(uploaded_file.read())

                session = SessionLocal()
                neues_fest = Fest(name=fest_name, excel_filename=filename, datum=fest_datum)
                session.add(neues_fest)
                session.commit()

                anzahl = importiere_excel_in_bestellungen(filename, neues_fest.id)
                st.success(f"✅ Fest *{fest_name}* wurde angelegt. {anzahl} Bestellungen importiert.")
                session.close()

    st.divider()
    st.subheader("📋 Bestehende Feste")

    session = SessionLocal()
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
                    if st.button("🗑️", key=f"delete_{fest.id}"):
                        session.query(Bestellung).filter_by(fest_id=fest.id).delete()
                        session.query(Einkauf).filter_by(fest_id=fest.id).delete()
                        session.delete(fest)
                        session.commit()
                        st.rerun()
            st.markdown("---")
