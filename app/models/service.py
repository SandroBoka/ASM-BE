from sqlalchemy import Column, Integer, Numeric, String, Text

from app.db.database import Base


class Service(Base):
    __tablename__ = "usluga"

    IdUsluge = Column(Integer, primary_key=True, index=True)

    NazivUsluge = Column(String(100), nullable=False)

    Opis = Column(Text, nullable=True)

    Trajanje = Column(Integer, nullable=False)

    Cijena = Column(Numeric(10, 2), nullable=False)
