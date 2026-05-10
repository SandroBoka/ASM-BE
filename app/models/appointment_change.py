from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class AppointmentChange(Base):
    __tablename__ = "promjena_termina"

    IdZahtjevaPromjene = Column(Integer, primary_key=True, index=True)

    DatumZahtjeva = Column(Date, nullable=False, server_default=func.current_date())

    Status = Column(String(20), nullable=False, default="na cekanju")

    KomentarZaposlenika = Column(Text, nullable=True)

    IdRezervacije = Column(
        Integer,
        ForeignKey("rezervacija.IdRezervacije", ondelete="CASCADE"),
        nullable=False
    )

    IdStarogTermina = Column(
        Integer,
        ForeignKey("termin.IdTermina"),
        nullable=False
    )

    IdNovogTermina = Column(
        Integer,
        ForeignKey("termin.IdTermina"),
        nullable=False
    )

    IdOsobe_Zaposlenik = Column(
        Integer,
        ForeignKey("zaposlenik.IdOsobe"),
        nullable=True
    )

    reservation = relationship("Reservation", back_populates="appointment_changes")

    old_appointment = relationship(
        "Appointment",
        foreign_keys=[IdStarogTermina],
        back_populates="old_appointment_changes"
    )

    new_appointment = relationship(
        "Appointment",
        foreign_keys=[IdNovogTermina],
        back_populates="new_appointment_changes"
    )

    employee = relationship("Employee", back_populates="processed_appointment_changes")
