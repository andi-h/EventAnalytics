import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from datenbank import SessionLocal, Fest, Bestellung, Einkauf, ProduktZutat, Zutat

st.set_page_config(page_title="Auswertung", page_icon="📊")

# Utility-Funktion zum Berechnen von Kennzahlen für ein Fest
def berechne_kennzahlen(fest_id: int, produkt_filter: list = None, station_filter: list = None):
    session = SessionLocal()

    # Bestellungen filtern
    bestellungen = session.query(Bestellung).filter_by(fest_id=fest_id)
    if station_filter:
        bestellungen = bestellungen.filter(Bestellung.station.in_(station_filter))
    if produkt_filter:
        bestellungen = bestellungen.filter(Bestellung.produkt.in_(produkt_filter))

    bestellungen = bestellungen.all()

    # Umsatz, Portionen
    umsatz = sum(b.preis * b.menge for b in bestellungen)
    portionen = sum(b.menge for b in bestellungen)

    # Einkaufskosten (nur Zutaten, die für das Fest auch verwendet wurden)
    produktnamen = list(set(b.produkt for b in bestellungen))
    zutaten_ids = session.query(ProduktZutat.zutat_id).filter(
        ProduktZutat.fest_id == fest_id,
        ProduktZutat.produkt.in_(produktnamen)
    ).distinct().all()
    zutaten_ids = [z[0] for z in zutaten_ids]

    einkaeufe = session.query(Einkauf).filter(
        Einkauf.fest_id == fest_id,
        Einkauf.zutat_id.in_(zutaten_ids)
    ).all()

    # Einkaufskosten korrekt berechnen (anteilig pro Produkt)
    verbrauch_pro_zutat = {}
    gesamtverbrauch_pro_zutat = {}

    for produkt in produktnamen:
        p_bestellungen = [b for b in bestellungen if b.produkt == produkt]
        menge_total = sum(b.menge for b in p_bestellungen)

        produktzutaten = session.query(ProduktZutat).filter_by(fest_id=fest_id, produkt=produkt).all()
        for pz in produktzutaten:
            verbraucht = pz.menge_pro_portion * menge_total
            if pz.zutat_id not in gesamtverbrauch_pro_zutat:
                gesamtverbrauch_pro_zutat[pz.zutat_id] = 0
            gesamtverbrauch_pro_zutat[pz.zutat_id] += verbraucht

            if produkt_filter is None or produkt in produkt_filter:
                if pz.zutat_id not in verbrauch_pro_zutat:
                    verbrauch_pro_zutat[pz.zutat_id] = 0
                verbrauch_pro_zutat[pz.zutat_id] += verbraucht

    # Schritt 2: Einkaufskosten anteilig nach Verbrauch verteilen
    einkaeufe = session.query(Einkauf).filter(
        Einkauf.fest_id == fest_id,
        Einkauf.zutat_id.in_(gesamtverbrauch_pro_zutat.keys())
    ).all()

    einkaufswert = 0
    zutat_preise = {}  # Für spätere Verwendung pro Produkt

    for einkauf in einkaeufe:
        zutat_id = einkauf.zutat_id
        if einkauf.menge_gekauft > 0:
            einheitskosten = einkauf.preis / (einkauf.menge_gekauft - einkauf.menge_zurueck)
            zutat_preise[zutat_id] = einheitskosten  # merken für spätere Berechnung pro Produkt
            verbrauch = verbrauch_pro_zutat.get(zutat_id, 0)
            einkaufswert += einheitskosten * verbrauch

    # Schritt 3: Gewinn pro Produkt mit anteiligen Einkaufskosten berechnen
    gewinn_pro_produkt = {}
    for produkt in produktnamen:
        if produkt_filter and produkt not in produkt_filter:
            continue  # Überspringen

        p_bestellungen = [b for b in bestellungen if b.produkt == produkt]
        menge_total = sum(b.menge for b in p_bestellungen)
        umsatz_p = sum(b.preis * b.menge for b in p_bestellungen)

        produktzutaten = session.query(ProduktZutat).filter_by(fest_id=fest_id, produkt=produkt).all()
        kosten_verkaufte_portionen = 0
        for pz in produktzutaten:
            einheitskosten = zutat_preise.get(pz.zutat_id, 0)
            kosten_verkaufte_portionen += einheitskosten * pz.menge_pro_portion * menge_total

        gewinn_pro_produkt[produkt] = {
            "umsatz": umsatz_p,
            "menge": menge_total,
            "einkauf": kosten_verkaufte_portionen,
            "gewinn": umsatz_p - kosten_verkaufte_portionen,
            "marge": (umsatz_p - kosten_verkaufte_portionen) / umsatz_p if umsatz_p > 0 else 0,
            "gewinn_pro_portion": (umsatz_p - kosten_verkaufte_portionen) / menge_total if menge_total > 0 else 0
        }

    gewinn = umsatz - einkaufswert

    gewinn_pro_portion = gewinn / portionen if portionen > 0 else 0

    session.close()
    return {
        "umsatz": umsatz,
        "einkauf": einkaufswert,
        "gewinn": gewinn,
        "marge": gewinn / umsatz if umsatz > 0 else 0,
        "portionen": portionen,
        "gewinn_pro_portion": gewinn_pro_portion,
        "gewinn_pro_produkt": gewinn_pro_produkt
    }

def show():
    # Streamlit-Seite: Auswertung
    st.title("📊 Auswertung eines Fests")
    session = SessionLocal()
    feste = session.query(Fest).order_by(Fest.datum.desc()).all()
    fest_optionen = {f"{f.festtyp.name}: {f.datum.strftime('%d.%m.%Y')}": f.id for f in feste}
    session.close()

    col1, col2 = st.columns(2)
    with col1:
        hauptfest_name = st.selectbox("Fest auswählen", list(fest_optionen.keys()), key="hauptfest")
    with col2:
        vergleich_name = st.selectbox("Vergleich mit Fest (optional)", ["–"] + list(fest_optionen.keys()), key="vergleichfest")

    hauptfest_id = fest_optionen[hauptfest_name]
    vergleich_id = fest_optionen.get(vergleich_name) if vergleich_name != "–" else None

    # Optionaler Produktfilter
    if vergleich_id:
        stationen = session.query(Bestellung.station).filter(or_(Bestellung.fest_id == hauptfest_id, Bestellung.fest_id == vergleich_id)).distinct().all()
        produkt_query = session.query(Bestellung.produkt).filter(or_(Bestellung.fest_id == hauptfest_id, Bestellung.fest_id == vergleich_id))
    else:
        stationen = session.query(Bestellung.station).filter(Bestellung.fest_id == hauptfest_id).distinct().all()
        produkt_query = session.query(Bestellung.produkt).filter(Bestellung.fest_id == hauptfest_id)
    
    session = SessionLocal()
    station_liste = sorted([s[0] for s in stationen if s[0]])
    station_filter = st.multiselect("Stationen filtern (optional)", options=station_liste)
    if station_filter:
        produkt_query = produkt_query.filter(Bestellung.station.in_(station_filter))
    produkte = produkt_query.distinct().all()
    session.close()
    produkt_liste = sorted([p[0] for p in produkte])
    produkt_filter = st.multiselect("Produkte filtern (optional)", options=produkt_liste)

    if not produkt_filter:
        produkt_filter = None

    # Kennzahlen berechnen
    k1 = berechne_kennzahlen(hauptfest_id, produkt_filter, station_filter)
    k2 = berechne_kennzahlen(vergleich_id, produkt_filter, station_filter) if vergleich_id else None

    st.markdown("## Kennzahlen")

    def format_delta(a, b):
        if b == 0:
            return "–"
        diff = a - b
        pct = (diff / b) * 100
        return f"{pct:.1f}%"

    def highlight_best(value, all_vals):
        if value == max(all_vals):
            return "🟢 Bester Wert bisher"
        elif value == min(all_vals):
            return "🔴 Schwächster Wert"
        else:
            return ""

    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        st.metric("Umsatz", f"{k1['umsatz']:.2f} €", format_delta(k1['umsatz'], k2['umsatz']) if k2 else None)
        st.metric("Einkaufskosten", f"{k1['einkauf']:.2f} €", format_delta(k1['einkauf'], k2['einkauf']) if k2 else None)
        st.metric("Gewinn", f"{k1['gewinn']:.2f} €", format_delta(k1['gewinn'], k2['gewinn']) if k2 else None)
    with col2:
        st.metric("Verkaufte Portionen", k1['portionen'], format_delta(k1['portionen'], k2['portionen']) if k2 else None)
        st.metric("Gewinn/Portion", f"{k1['gewinn_pro_portion']:.2f} €", format_delta(k1['gewinn_pro_portion'], k2['gewinn_pro_portion']) if k2 else None)
        st.metric("Marge", f"{100*k1['marge']:.2f} %", format_delta(k1['marge'], k2['marge']) if k2 else None)
    with col3:
        # Könnte später um echten Bestwertvergleich erweitert werden
        pass

    st.markdown("### Produkte")
    produkt_tabelle = pd.DataFrame.from_dict(k1['gewinn_pro_produkt'], orient='index')
    produkt_tabelle = produkt_tabelle.sort_values(by="gewinn", ascending=False)
    st.dataframe(produkt_tabelle, 
                 use_container_width=True,
                 column_config={
                    "umsatz": st.column_config.NumberColumn(
                        "Umsatz",                # header label
                        help="Umsatz in Euro",   # tooltip
                        format="%.1f €"          # display format
                    ),
                    "menge": st.column_config.NumberColumn(
                        "Portionen",
                        help="Anzahl der verkauften Portionen"
                    ),
                    "einkauf": st.column_config.NumberColumn(
                        "Kosten",
                        help="Einkaufskosten in Euro", 
                        format="%.1f €"
                    ),
                    "gewinn": st.column_config.NumberColumn(
                        "Gewinn",
                        help="Gewinn in Euro", 
                        format="%.1f €"
                    ),
                    "marge": st.column_config.NumberColumn(
                        "Marge",
                        help="Marge in Prozent",
                        format="percent"
                    ),
                    "gewinn_pro_portion": st.column_config.NumberColumn(
                        "Gewinn/Portion",
                        help="Gewinn pro Portion in Euro", 
                        format="%.2f €"
                    ),
                }
    )
