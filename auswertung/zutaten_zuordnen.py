import streamlit as st
from datenbank import SessionLocal, Zutat, ProduktZutat, Fest
from sqlalchemy.orm import joinedload

def show(session, feste, aktuelles_fest):
    st.subheader("🥣 Zutaten zu Produkten zuordnen")

    # Alle vorherigen Feste sortiert absteigend (außer aktuelles)
    frühere_feste = [f for f in feste if f.datum < aktuelles_fest.datum]

    # Zutaten-Liste
    zutaten = session.query(Zutat).order_by(Zutat.name).all()
    zutat_dict = {z.id: z for z in zutaten}
    zutat_anzeige = {z.id: f"{z.name} ({z.einheit})" for z in zutaten}

    # Produkte im aktuellen Fest
    produkte = sorted(list({b.produkt for b in aktuelles_fest.bestellungen}))

    # Automatische Übernahme aus früheren Festen (nur wenn noch keine Zuweisung)
    bestehende_zuweisungen = session.query(ProduktZutat).filter_by(fest_id=aktuelles_fest.id).all()
    bestehende_keys = {(pz.produkt, pz.zutat_id) for pz in bestehende_zuweisungen}

    if not bestehende_zuweisungen:
        for produkt in produkte:
            for fest in frühere_feste:
                alte_zuweisungen = session.query(ProduktZutat).filter_by(fest_id=fest.id, produkt=produkt).all()
                for alt in alte_zuweisungen:
                    key = (alt.produkt, alt.zutat_id)
                    if key not in bestehende_keys:
                        kopie = ProduktZutat(
                            fest_id=aktuelles_fest.id,
                            produkt=alt.produkt,
                            zutat_id=alt.zutat_id,
                            menge_pro_portion=alt.menge_pro_portion
                        )
                        session.add(kopie)
                        bestehende_keys.add(key)
    session.commit()

    # Zuweisung pro Produkt
    for produkt in produkte:
        st.markdown(f"### 🧾 **{produkt}**")

        with st.form(f"form_{produkt}"):
            col1, col2, col3 = st.columns([5, 2, 2])

            # Auswahl der Zutat (mit dynamischer Einheit)
            zutat_id = col1.selectbox(
                "Zutat auswählen",
                options=list(zutat_dict.keys()),
                format_func=lambda i: zutat_anzeige[i],
                key=f"zutat_{produkt}"
            )

            menge = col2.number_input(
                f"Menge pro Portion",
                min_value=0.0,
                step=0.1,
                key=f"menge_{produkt}"
            )

            with col3:
                # Add vertical spacer (adjust height as needed)
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                speichern = st.form_submit_button("➕ Speichern")

            if speichern:
                vorhandene = session.query(ProduktZutat).filter_by(
                    fest_id=aktuelles_fest.id, produkt=produkt, zutat_id=zutat_id
                ).first()

                if vorhandene:
                    vorhandene.menge_pro_portion = menge
                else:
                    neue = ProduktZutat(
                        fest_id=aktuelles_fest.id,
                        produkt=produkt,
                        zutat_id=zutat_id,
                        menge_pro_portion=menge
                    )
                    session.add(neue)
                session.commit()
                st.rerun()

        # Table Header
        header1, header2, header3 = st.columns([5, 2, 1])
        header1.markdown("**Zutat**")
        header2.markdown("**Menge pro Portion**")
        header3.markdown("**Aktion**")

        # Table Rows
        zuweisungen = session.query(ProduktZutat).options(joinedload(ProduktZutat.zutat)) \
            .filter_by(fest_id=aktuelles_fest.id, produkt=produkt).all()

        for z in zuweisungen:
            col1, col2, col3 = st.columns([5, 2, 1])
            col1.markdown(f"{z.zutat.name}")
            col2.markdown(f"{z.menge_pro_portion} {z.zutat.einheit}")
            if col3.button("🗑️", key=f"del_{produkt}_{z.zutat_id}"):
                session.delete(z)
                session.commit()
                st.rerun()

    session.close()
