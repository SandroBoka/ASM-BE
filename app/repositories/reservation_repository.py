from typing import cast

from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.reservation_service import ReservationService


class ReservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, reservation_id: int) -> Reservation | None:
        return (
            self.db
            .query(Reservation)
            .filter(Reservation.IdRezervacije == reservation_id)  # type: ignore[arg-type]
            .first()
        )

    def get_all(self) -> list[Reservation]:
        return cast(
            list[Reservation],
            self.db
            .query(Reservation)
            .order_by(Reservation.DatumKreiranja, Reservation.IdRezervacije)
            .all()
        )

    def get_by_customer_id(self, person_id: int) -> list[Reservation]:
        return cast(
            list[Reservation],
            self.db
            .query(Reservation)
            .filter(Reservation.IdOsobe_Korisnik == person_id)  # type: ignore[arg-type]
            .order_by(Reservation.DatumKreiranja, Reservation.IdRezervacije)
            .all()
        )

    def get_by_status(self, status: str) -> list[Reservation]:
        return cast(
            list[Reservation],
            self.db
            .query(Reservation)
            .filter(Reservation.Status == status)  # type: ignore[arg-type]
            .order_by(Reservation.DatumKreiranja, Reservation.IdRezervacije)
            .all()
        )

    def get_approved_by_appointment_id(
            self,
            appointment_id: int
    ) -> Reservation | None:
        return (
            self.db
            .query(Reservation)
            .filter(Reservation.IdTermina == appointment_id)  # type: ignore[arg-type]
            .filter(Reservation.Status == "odobrena")  # type: ignore[arg-type]
            .first()
        )

    def create(self, reservation: Reservation) -> Reservation:
        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def add_service(
            self,
            reservation_service: ReservationService
    ) -> ReservationService:
        self.db.add(reservation_service)
        self.db.commit()
        self.db.refresh(reservation_service)
        return reservation_service

    def update(self, reservation: Reservation) -> Reservation:
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def delete(self, reservation: Reservation) -> None:
        self.db.delete(reservation)
        self.db.commit()
