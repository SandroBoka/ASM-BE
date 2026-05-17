from sqlalchemy.orm import Session
from app.models.service import Service
from typing import cast


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, search: str | None = None) -> list[Service]:
        query = self.db.query(Service)

        if search:
            query = query.filter(Service.NazivUsluge.ilike(f"%{search}%"))

        return cast(list[Service], query.order_by(Service.IdUsluge).all())

    def get_by_id(self, service_id: int) -> Service | None:
        return (
            self.db
            .query(Service)
            .filter(Service.IdUsluge == service_id)  # type: ignore[arg-type]
            .first()
        )

    def get_by_name_case_insensitive(self, name: str) -> Service | None:
        return (
            self.db
            .query(Service)
            .filter(Service.NazivUsluge.ilike(name.strip()))
            .first()
        )

    def create(self, service: Service) -> Service:
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def update(self, service: Service) -> Service:
        self.db.commit()
        self.db.refresh(service)
        return service

    def delete(self, service: Service) -> None:
        self.db.delete(service)
        self.db.commit()
