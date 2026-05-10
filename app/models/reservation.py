from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Reservation(Base):
    __tablename__ = "rezervacija"

    IdRezervacije = Column(Integer, primary_key=True, index=True)

    DatumKreiranja = Column(Date, nullable=False, server_default=func.current_date())

    Status = Column(String(20), nullable=False, default="na cekanju")

    KilometrazaVozila = Column(Integer, nullable=False)

    OpisProblema = Column(Text, nullable=False)

    KomentarZaposlenika = Column(Text, nullable=True)

    IdOsobe_Korisnik = Column(Integer, ForeignKey("korisnik.IdOsobe"), nullable=False)

    IdTermina = Column(Integer, ForeignKey("termin.IdTermina"), nullable=False)

    IdVozila = Column(Integer, ForeignKey("vozilo.IdVozila"), nullable=False)

    IdOsobe_Zaposlenik = Column(Integer, ForeignKey("zaposlenik.IdOsobe"), nullable=True)

    customer = relationship("Customer", back_populates="reservations")

    appointment = relationship("Appointment", back_populates="reservations")

    vehicle = relationship("Vehicle", back_populates="reservations")

    employee = relationship("Employee", back_populates="processed_reservations")

    reservation_services = relationship("ReservationService", back_populates="reservation")

    appointment_changes = relationship("AppointmentChange", back_populates="reservation")

    notifications = relationship("Notification", back_populates="reservation")
