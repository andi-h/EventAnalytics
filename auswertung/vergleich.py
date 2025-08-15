import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from datenbank import SessionLocal, Fest, Bestellung, Einkauf
import altair as alt

def show(session, feste, aktuelles_fest):
    st.title("📈 Vergleich der Feste")

    vergleichsdaten = []

    for fest in feste:
        # Umsatz und Portionen
        bestellungen = session.query(Bestellung).filter_by(fest_id=fest.id, storniert=False).all()
        umsatz = sum(b.preis * b.menge for b in bestellungen if b.bezahlt)
        portionen = sum(b.menge for b in bestellungen)

        # Einkaufskosten
        einkaeufe = session.query(Einkauf).filter_by(fest_id=fest.id).all()
        einkaufswert = sum(e.preis for e in einkaeufe)

        gewinn = umsatz - einkaufswert
        gewinn_pro_portion = gewinn / portionen if portionen > 0 else 0

        vergleichsdaten.append({
            "Datum": fest.datum.date(),
            "Fest": fest.festtyp.name,
            "Umsatz": umsatz,
            "Einkauf": einkaufswert,
            "Gewinn": gewinn,
            "Portionen": portionen,
            "Gewinn/Portion": gewinn_pro_portion
        })

    session.close()

    # DataFrame erstellen
    df = pd.DataFrame(vergleichsdaten)

    # Diagrammwahl
    kennzahlen = ["Umsatz", "Einkauf", "Gewinn", "Portionen", "Gewinn/Portion"]
    kennzahl = st.selectbox("Kennzahl auswählen", kennzahlen)

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Datum:T", title="Datum"),
        y=alt.Y(f"{kennzahl}:Q", title=kennzahl),
        tooltip=["Fest", "Datum", kennzahl]
    ).properties(
        width=700,
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    st.dataframe(df.set_index("Fest"), use_container_width=True)
