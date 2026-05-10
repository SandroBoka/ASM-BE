from sqlalchemy import Column, Date, Integer, String, Time
from sqlalchemy.orm import relationship

from app.db.database import Base


class Appointment(Base):
    __tablename__ = "termin"

    IdTermina = Column(Integer, primary_key=True, index=True)

    Datum = Column(Date, nullable=False)

    VrijemeOd = Column(Time, nullable=False)

    VrijemeDo = Column(Time, nullable=False)

    Status = Column(String(20), nullable=False, default="slobodan")

    reservations = relationship("Reservation", back_populates="appointment")

    old_appointment_changes = relationship(
        "AppointmentChange",
        foreign_keys="AppointmentChange.IdStarogTermina",
        back_populates="old_appointment"
    )

    new_appointment_changes = relationship(
        "AppointmentChange",
        foreign_keys="AppointmentChange.IdNovogTermina",
        back_populates="new_appointment"
    )
