import streamlit as st
from datenbank import SessionLocal, Fest, ProduktZutat, Einkauf, Zutat
from sqlalchemy.orm import joinedload

def show(session, feste, aktuelles_fest):
    st.subheader("🛒 Einkäufe für das Fest erfassen")

    # Zutaten ermitteln, die für das Fest relevant sind (ProduktZutat)
    zutaten_ids = session.query(ProduktZutat.zutat_id).filter_by(fest_id=aktuelles_fest.id).distinct().all()
    zutaten_ids = [z[0] for z in zutaten_ids]

    if not zutaten_ids:
        st.info("Keine Zutaten für dieses Fest gefunden. Bitte zuerst Zutaten zu Produkten zuordnen.")
        session.close()
        st.stop()

    zutaten = session.query(Zutat).filter(Zutat.id.in_(zutaten_ids)).order_by(Zutat.name).all()

    st.markdown(f"### Einkaufsliste für {aktuelles_fest.festtyp.name}")

    # Einkaufseinträge laden (für die Zutaten)
    einkaufsdaten = {
        einkauf.zutat_id: einkauf
        for einkauf in session.query(Einkauf).filter_by(fest_id=aktuelles_fest.id).all()
    }

    form = st.form("einkaeufe_form")
    eingaben = {}

    for z in zutaten:
        st.markdown(f"**{z.name} ({z.einheit})**")
        col1, col2, col3 = st.columns(3)

        mitgekauft = eingaben.get(z.id, {})
        eingaben[z.id] = {
            "menge_gekauft": col1.number_input(
                "Menge gekauft", min_value=0.0, step=0.1,
                value=einkaufsdaten.get(z.id).menge_gekauft if einkaufsdaten.get(z.id) else 0.0,
                key=f"gekauft_{z.id}"
            ),
            "menge_zurueck": col2.number_input(
                "Menge zurück", min_value=0.0, step=0.1,
                value=einkaufsdaten.get(z.id).menge_zurueck if einkaufsdaten.get(z.id) else 0.0,
                key=f"zurueck_{z.id}"
            ),
            "preis": col3.number_input(
                "Preis (€)", min_value=0.0, step=0.01,
                value=einkaufsdaten.get(z.id).preis if einkaufsdaten.get(z.id) else 0.0,
                format="%.2f",
                key=f"preis_{z.id}"
            )
        }

    submit = form.form_submit_button("💾 Einkäufe speichern")

    if submit:
        for zutat_id, daten in eingaben.items():
            einkauf = einkaufsdaten.get(zutat_id)
            if einkauf:
                einkauf.menge_gekauft = daten["menge_gekauft"]
                einkauf.menge_zurueck = daten["menge_zurueck"]
                einkauf.preis = daten["preis"]
            else:
                einkauf = Einkauf(
                    fest_id=aktuelles_fest.id,
                    zutat_id=zutat_id,
                    menge_gekauft=daten["menge_gekauft"],
                    menge_zurueck=daten["menge_zurueck"],
                    preis=daten["preis"]
                )
                session.add(einkauf)
        session.commit()
        st.success("Einkäufe wurden gespeichert!")

    session.close()
