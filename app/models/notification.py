from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Notification(Base):
    __tablename__ = "obavijest"

    IdObavijesti = Column(Integer, primary_key=True, index=True)

    Naslov = Column(String(200), nullable=False)

    Tekst = Column(Text, nullable=False)

    DatumSlanja = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    Procitana = Column(Boolean, nullable=False, default=False)

    IdOsobe = Column(
        Integer,
        ForeignKey("korisnik.IdOsobe"),
        nullable=False
    )

    IdRezervacije = Column(
        Integer,
        ForeignKey("rezervacija.IdRezervacije"),
        nullable=False
    )

    customer = relationship("Customer", back_populates="notifications")

    reservation = relationship("Reservation", back_populates="notifications")
