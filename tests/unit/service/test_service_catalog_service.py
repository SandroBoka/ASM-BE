import pytest
from fastapi import HTTPException

from app.models.service import Service
from app.services.service_catalog_service import ServiceCatalogService


class FakeServiceRepository:
    def __init__(self):
        self.services = []
        self.next_id = 1

    def get_all(self, search=None):
        if search is None:
            return self.services

        return [
            service for service in self.services
            if search.lower() in service.NazivUsluge.lower()
        ]

    def get_by_id(self, service_id):
        for service in self.services:
            if service.IdUsluge == service_id:
                return service

        return None

    def create(self, service):
        service.IdUsluge = self.next_id
        self.next_id += 1
        self.services.append(service)
        return service

    def update(self, service):
        return service

    def delete(self, service):
        self.services.remove(service)


def test_create_service_success():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    service = service_catalog.create_service(
        naziv_usluge="Redovni servis",
        opis="Zamjena ulja i filtera",
        trajanje=60,
        cijena=150
    )

    assert service.IdUsluge == 1
    assert service.NazivUsluge == "Redovni servis"
    assert service.Opis == "Zamjena ulja i filtera"
    assert service.Trajanje == 60
    assert service.Cijena == 150


def test_create_service_fails_when_name_is_too_short():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    with pytest.raises(HTTPException) as error:
        service_catalog.create_service(
            naziv_usluge="AB",
            opis=None,
            trajanje=60,
            cijena=150
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Naziv usluge mora imati barem 3 znaka."


def test_create_service_fails_when_duration_is_zero():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    with pytest.raises(HTTPException) as error:
        service_catalog.create_service(
            naziv_usluge="Redovni servis",
            opis=None,
            trajanje=0,
            cijena=150
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Trajanje usluge mora biti veće od 0 minuta."


def test_create_service_fails_when_price_is_negative():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    with pytest.raises(HTTPException) as error:
        service_catalog.create_service(
            naziv_usluge="Redovni servis",
            opis=None,
            trajanje=60,
            cijena=-10
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Cijena usluge ne može biti negativna."


def test_get_service_by_id_success():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    created_service = service_catalog.create_service(
        naziv_usluge="Dijagnostika",
        opis="Kompjuterska dijagnostika",
        trajanje=30,
        cijena=50
    )

    found_service = service_catalog.get_service_by_id(created_service.IdUsluge)

    assert found_service.IdUsluge == created_service.IdUsluge
    assert found_service.NazivUsluge == "Dijagnostika"


def test_get_service_by_id_fails_when_service_does_not_exist():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    with pytest.raises(HTTPException) as error:
        service_catalog.get_service_by_id(999)

    assert error.value.status_code == 404
    assert error.value.detail == "Usluga nije pronađena."


def test_search_services_by_name():
    repository = FakeServiceRepository()
    service_catalog = ServiceCatalogService(repository)

    service_catalog.create_service(
        naziv_usluge="Redovni servis",
        opis=None,
        trajanje=60,
        cijena=150
    )

    service_catalog.create_service(
        naziv_usluge="Dijagnostika",
        opis=None,
        trajanje=30,
        cijena=50
    )

    results = service_catalog.get_all_services(search="servis")

    assert len(results) == 1
    assert results[0].NazivUsluge == "Redovni servis"
