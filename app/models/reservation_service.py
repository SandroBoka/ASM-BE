from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.database import Base


class ReservationService(Base):
    __tablename__ = "rezervacija_usluga"

    IdRezervacije = Column(
        Integer,
        ForeignKey("rezervacija.IdRezervacije", ondelete="CASCADE"),
        primary_key=True
    )

    IdUsluge = Column(Integer, ForeignKey("usluga.IdUsluge"), primary_key=True)

    Kolicina = Column(Integer, nullable=False, default=1)

    reservation = relationship("Reservation", back_populates="reservation_services")

    service = relationship("Service", back_populates="reservation_services")
