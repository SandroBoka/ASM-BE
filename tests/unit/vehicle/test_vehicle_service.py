import pytest
from fastapi import HTTPException

from app.services.vehicle_service import VehicleService


class FakeVehicleRepository:
    def __init__(self):
        self.vehicles = []
        self.next_id = 1

    def get_by_id(self, vehicle_id):
        for vehicle in self.vehicles:
            if vehicle.IdVozila == vehicle_id:
                return vehicle
        return None

    def get_by_registration(self, registration):
        for vehicle in self.vehicles:
            if vehicle.RegOznaka == registration:
                return vehicle
        return None

    def get_by_customer_id(self, person_id):
        return [
            vehicle
            for vehicle in self.vehicles
            if vehicle.IdOsobe == person_id
        ]

    def create(self, vehicle):
        vehicle.IdVozila = self.next_id
        self.next_id += 1
        self.vehicles.append(vehicle)
        return vehicle

    def update(self, vehicle):
        return vehicle

    def delete(self, vehicle):
        self.vehicles.remove(vehicle)


def test_create_vehicle():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    vehicle = service.create_vehicle(
        marka="Volkswagen",
        model="Golf",
        godina=2018,
        vrsta_motora="diesel",
        reg_oznaka="ZG-123-AB",
        id_osobe=1
    )

    assert vehicle.IdVozila == 1
    assert vehicle.Marka == "Volkswagen"
    assert vehicle.Model == "Golf"
    assert vehicle.Godina == 2018
    assert vehicle.VrstaMotora == "diesel"
    assert vehicle.RegOznaka == "ZG-123-AB"
    assert vehicle.IdOsobe == 1


def test_create_vehicle_fails_when_registration_exists():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    service.create_vehicle(
        marka="Volkswagen",
        model="Golf",
        godina=2018,
        vrsta_motora="diesel",
        reg_oznaka="ZG-123-AB",
        id_osobe=1
    )

    with pytest.raises(HTTPException) as error:
        service.create_vehicle(
            marka="Audi",
            model="A4",
            godina=2020,
            vrsta_motora="benzin",
            reg_oznaka="ZG-123-AB",
            id_osobe=1
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Registracijska oznaka je već u uporabi."


def test_create_vehicle_fails_when_year_is_invalid():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    with pytest.raises(HTTPException) as error:
        service.create_vehicle(
            marka="Volkswagen",
            model="Golf",
            godina=1800,
            vrsta_motora="diesel",
            reg_oznaka="ZG-123-AB",
            id_osobe=1
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Godina vozila mora biti između 1900 i 2100."


def test_get_vehicle_by_id_fails_when_vehicle_does_not_exist():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    with pytest.raises(HTTPException) as error:
        service.get_vehicle_by_id(999)

    assert error.value.status_code == 404
    assert error.value.detail == "Vozilo nije pronađeno."


def test_get_vehicles_by_customer_id():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    service.create_vehicle(
        marka="Volkswagen",
        model="Golf",
        godina=2018,
        vrsta_motora="diesel",
        reg_oznaka="ZG-123-AB",
        id_osobe=1
    )

    service.create_vehicle(
        marka="Audi",
        model="A4",
        godina=2020,
        vrsta_motora="benzin",
        reg_oznaka="ZG-456-CD",
        id_osobe=2
    )

    vehicles = service.get_vehicles_by_customer_id(1)

    assert len(vehicles) == 1
    assert vehicles[0].RegOznaka == "ZG-123-AB"


def test_update_vehicle():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    vehicle = service.create_vehicle(
        marka="Volkswagen",
        model="Golf",
        godina=2018,
        vrsta_motora="diesel",
        reg_oznaka="ZG-123-AB",
        id_osobe=1
    )

    updated_vehicle = service.update_vehicle(
        vehicle_id=vehicle.IdVozila,
        marka="Volkswagen",
        model="Passat",
        godina=2021,
        vrsta_motora="benzin",
        reg_oznaka="ZG-999-ZZ"
    )

    assert updated_vehicle.IdVozila == vehicle.IdVozila
    assert updated_vehicle.Model == "Passat"
    assert updated_vehicle.Godina == 2021
    assert updated_vehicle.VrstaMotora == "benzin"
    assert updated_vehicle.RegOznaka == "ZG-999-ZZ"


def test_delete_vehicle():
    repository = FakeVehicleRepository()
    service = VehicleService(repository)

    vehicle = service.create_vehicle(
        marka="Volkswagen",
        model="Golf",
        godina=2018,
        vrsta_motora="diesel",
        reg_oznaka="ZG-123-AB",
        id_osobe=1
    )

    service.delete_vehicle(vehicle.IdVozila)

    assert repository.get_by_id(vehicle.IdVozila) is None
