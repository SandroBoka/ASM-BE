from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Vehicle(Base):
    __tablename__ = "vozilo"

    IdVozila = Column(Integer, primary_key=True, index=True)

    Marka = Column(String(50), nullable=False)

    Model = Column(String(50), nullable=False)

    Godina = Column(Integer, nullable=False)

    VrstaMotora = Column(String(50), nullable=False)

    RegOznaka = Column(String(20), nullable=False, unique=True, index=True)

    IdOsobe = Column(Integer, ForeignKey("korisnik.IdOsobe", ondelete="CASCADE"), nullable=False)

    customer = relationship("Customer", back_populates="vehicles")

    reservations = relationship("Reservation", back_populates="vehicle")
