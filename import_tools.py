# import_tools.py
import pandas as pd
from datenbank import Bestellung, SessionLocal
import streamlit as st

def importiere_excel_in_bestellungen(excel_path, fest_id):
    df = pd.read_excel(excel_path)
    df.columns = [col.strip() for col in df.columns]

    bestellungen = []
    for _, row in df.iterrows():
        try:
            if pd.isna(row.get("ZeileNr")) or str(row.get("ZeileNr")).strip() == "":
                continue
            #elif int(row.get("storniert", 0)) > 1:
            #    continue
            #elif int(row.get("Anzahl", 0)) < 1:
            #    continue
            bestellung = Bestellung(
                kellner=row.get("Kellner", ""),
                produkt=row.get("Produkt", ""),
                station=row.get("Station", ""),
                kommentar=row.get("Produktkommentar", ""),
                preis=float(row.get("Preis", 0)),
                menge=int(row.get("Anzahl", 1)),
                storniert=int(row.get("storniert", 0)),
                bezahlt=int(row.get("bezahlt", 1)),
                erstellt=pd.to_datetime(row.get("erstellt")),
                fest_id=fest_id
            )
            bestellungen.append(bestellung)
        except Exception as e:
            st.error(f"❌ Fehler beim Verarbeiten der Zeile Nr {str(row.get("ZeileNr"))}: {e}")

    session = SessionLocal()
    session.add_all(bestellungen)
    session.commit()
    session.close()
    return len(bestellungen)
