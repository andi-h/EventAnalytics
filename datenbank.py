from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey, Boolean, DateTime
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os

Base = declarative_base()

# Tabellen
class FestTyp(Base):
    __tablename__ = 'festtypen'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    feste = relationship('Fest', back_populates='festtyp')

class Fest(Base):
    __tablename__ = 'feste'
    id = Column(Integer, primary_key=True)
    datum = Column(DateTime, default=datetime.datetime.now())
    excel_filename = Column(String)
    festtyp_id = Column(Integer, ForeignKey('festtypen.id')) 

    bestellungen = relationship('Bestellung', back_populates='fest')
    rohstoffe = relationship('Einkauf', back_populates='fest')
    festtyp = relationship('FestTyp', back_populates='feste')

class Bestellung(Base):
    __tablename__ = 'bestellungen'
    id = Column(Integer, primary_key=True)
    kellner = Column(String)
    produkt = Column(String)
    station = Column(String)
    kommentar = Column(String)
    preis = Column(Float)
    menge = Column(Integer)
    storniert = Column(Integer)
    bezahlt = Column(Integer)
    erstellt = Column(DateTime)
    fest_id = Column(Integer, ForeignKey('feste.id'))

    fest = relationship('Fest', back_populates='bestellungen')


class Zutat(Base):
    __tablename__ = 'zutaten'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    einheit = Column(String)  # z.B. g, l, Stück


class ProduktZutat(Base):
    __tablename__ = 'produkt_zutat'
    id = Column(Integer, primary_key=True)
    fest_id = Column(Integer, ForeignKey('feste.id'))   # Neu: Bezug zum Fest
    produkt = Column(String)  # Name wie in Bestellung
    zutat_id = Column(Integer, ForeignKey('zutaten.id'))
    menge_pro_portion = Column(Float)

    zutat = relationship('Zutat')
    fest = relationship('Fest')



class Einkauf(Base):
    __tablename__ = "einkaeufe"

    id = Column(Integer, primary_key=True)
    fest_id = Column(Integer, ForeignKey("feste.id"))
    zutat_id = Column(Integer, ForeignKey("zutaten.id"))
    
    menge_gekauft = Column(Float)
    menge_zurueck = Column(Float)
    preis = Column(Float)

    zutat = relationship("Zutat")
    fest = relationship("Fest")


# Datenbank Setup
os.makedirs("data", exist_ok=True)  # sicherstellen, dass Ordner existiert
engine = create_engine('sqlite:///data/festdaten.db', echo=False)
SessionLocal = sessionmaker(bind=engine)

# DB initialisieren
def init_db():
    Base.metadata.create_all(engine)

# Direkt bei Import initialisieren
init_db()
