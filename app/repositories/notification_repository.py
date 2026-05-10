from typing import cast

from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, notification_id: int) -> Notification | None:
        return (
            self.db
            .query(Notification)
            .filter(Notification.IdObavijesti == notification_id)  # type: ignore[arg-type]
            .first()
        )

    def get_all(self) -> list[Notification]:
        return cast(
            list[Notification],
            self.db
            .query(Notification)
            .order_by(Notification.DatumSlanja, Notification.IdObavijesti)
            .all()
        )

    def get_by_customer_id(self, person_id: int) -> list[Notification]:
        return cast(
            list[Notification],
            self.db
            .query(Notification)
            .filter(Notification.IdOsobe == person_id)  # type: ignore[arg-type]
            .order_by(Notification.DatumSlanja, Notification.IdObavijesti)
            .all()
        )

    def get_by_reservation_id(self, reservation_id: int) -> list[Notification]:
        return cast(
            list[Notification],
            self.db
            .query(Notification)
            .filter(Notification.IdRezervacije == reservation_id)  # type: ignore[arg-type]
            .order_by(Notification.DatumSlanja, Notification.IdObavijesti)
            .all()
        )

    def get_unread_by_customer_id(self, person_id: int) -> list[Notification]:
        return cast(
            list[Notification],
            self.db
            .query(Notification)
            .filter(Notification.IdOsobe == person_id)  # type: ignore[arg-type]
            .filter(Notification.Procitana.is_(False))
            .order_by(Notification.DatumSlanja, Notification.IdObavijesti)
            .all()
        )

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def update(self, notification: Notification) -> Notification:
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete(self, notification: Notification) -> None:
        self.db.delete(notification)
        self.db.commit()
