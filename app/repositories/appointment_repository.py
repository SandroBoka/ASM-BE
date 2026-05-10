from datetime import date
from typing import cast

from sqlalchemy.orm import Session

from app.models.appointment import Appointment


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int) -> Appointment | None:
        return (
            self.db
            .query(Appointment)
            .filter(Appointment.IdTermina == appointment_id)  # type: ignore[arg-type]
            .first()
        )

    def get_all(self) -> list[Appointment]:
        return cast(
            list[Appointment],
            self.db
            .query(Appointment)
            .order_by(Appointment.Datum, Appointment.VrijemeOd)
            .all()
        )

    def get_available(
            self,
            date_from: date | None = None,
            date_to: date | None = None
    ) -> list[Appointment]:
        query = (
            self.db
            .query(Appointment)
            .filter(Appointment.Status == "slobodan")  # type: ignore[arg-type]
        )

        if date_from is not None:
            query = query.filter(Appointment.Datum >= date_from)

        if date_to is not None:
            query = query.filter(Appointment.Datum <= date_to)

        return cast(
            list[Appointment],
            query.order_by(Appointment.Datum, Appointment.VrijemeOd).all()
        )

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def update(self, appointment: Appointment) -> Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def delete(self, appointment: Appointment) -> None:
        self.db.delete(appointment)
        self.db.commit()
