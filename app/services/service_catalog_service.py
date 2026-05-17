from fastapi import HTTPException, status
from decimal import Decimal

from app.models.service import Service
from app.repositories.service_repository import ServiceRepository


class ServiceCatalogService:

    def __init__(self, repository: ServiceRepository):
        self.repository = repository

    def get_all_services(self, search: str | None = None) -> list[Service]:
        return self.repository.get_all(search=search)

    def get_service_by_id(self, service_id: int) -> Service:
        service = self.repository.get_by_id(service_id)

        if service is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usluga nije pronađena."
            )

        return service

    def create_service(
            self,
            naziv_usluge: str,
            opis: str | None,
            trajanje: int,
            cijena: Decimal
    ) -> Service:
        self._validate_service_data(
            naziv_usluge=naziv_usluge,
            trajanje=trajanje,
            cijena=cijena
        )
        self._check_name_uniqueness(naziv_usluge=naziv_usluge)

        service = Service(
            NazivUsluge=naziv_usluge,
            Opis=opis,
            Trajanje=trajanje,
            Cijena=cijena
        )

        return self.repository.create(service)

    def update_service(
            self,
            service_id: int,
            naziv_usluge: str,
            opis: str | None,
            trajanje: int,
            cijena: Decimal
    ) -> Service:
        service = self.get_service_by_id(service_id)

        self._validate_service_data(
            naziv_usluge=naziv_usluge,
            trajanje=trajanje,
            cijena=cijena
        )
        self._check_name_uniqueness(naziv_usluge=naziv_usluge, exclude_id=service_id)

        service.NazivUsluge = naziv_usluge
        service.Opis = opis
        service.Trajanje = trajanje
        service.Cijena = cijena

        return self.repository.update(service)

    def delete_service(self, service_id: int) -> None:
        service = self.get_service_by_id(service_id)
        self.repository.delete(service)

    @staticmethod
    def _validate_service_data(
            naziv_usluge: str,
            trajanje: int,
            cijena: Decimal
    ) -> None:
        if len(naziv_usluge.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Naziv usluge mora imati barem 3 znaka."
            )

        if trajanje <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trajanje usluge mora biti veće od 0 minuta."
            )

        if cijena < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cijena usluge ne može biti negativna."
            )

    def _check_name_uniqueness(
            self,
            naziv_usluge: str,
            exclude_id: int | None = None,
    ) -> None:
        existing = self.repository.get_by_name_case_insensitive(naziv_usluge)
        if existing is None:
            return
        if exclude_id is not None and existing.IdUsluge == exclude_id:
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Usluga s nazivom '{naziv_usluge.strip()}' već postoji."
        )
