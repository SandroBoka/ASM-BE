from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import settings
from app.db.database import Base
from app.models.appointment import Appointment
from app.repositories.appointment_repository import AppointmentRepository

engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def create_appointment(
        repository: AppointmentRepository,
        appointment_date: date = date(2026, 6, 1),
        vrijeme_od: time = time(8, 0),
        vrijeme_do: time = time(9, 0),
        status_value: str = "slobodan",
) -> Appointment:
    return repository.create(Appointment(
        Datum=appointment_date,
        VrijemeOd=vrijeme_od,
        VrijemeDo=vrijeme_do,
        Status=status_value,
    ))


def test_create_appointment_in_database():
    db = TestingSessionLocal()
    repository = AppointmentRepository(db)

    appointment = create_appointment(repository)

    assert appointment.IdTermina is not None
    assert appointment.Datum == date(2026, 6, 1)
    assert appointment.VrijemeOd == time(8, 0)
    assert appointment.Status == "slobodan"

    db.close()


def test_get_appointment_by_id_from_database():
    db = TestingSessionLocal()
    repository = AppointmentRepository(db)

    appointment = create_appointment(repository)

    found_appointment = repository.get_by_id(appointment.IdTermina)

    assert found_appointment is not None
    assert found_appointment.IdTermina == appointment.IdTermina

    db.close()


def test_get_all_appointments_orders_by_date_and_start_time():
    db = TestingSessionLocal()
    repository = AppointmentRepository(db)

    second = create_appointment(
        repository,
        appointment_date=date(2026, 6, 2),
        vrijeme_od=time(10, 0),
    )
    first = create_appointment(
        repository,
        appointment_date=date(2026, 6, 1),
        vrijeme_od=time(8, 0),
    )
    third = create_appointment(
        repository,
        appointment_date=date(2026, 6, 2),
        vrijeme_od=time(12, 0),
    )

    appointments = repository.get_all()

    assert [appointment.IdTermina for appointment in appointments] == [
        first.IdTermina,
        second.IdTermina,
        third.IdTermina,
    ]

    db.close()


def test_get_available_filters_by_status_and_date_range():
    db = TestingSessionLocal()
    repository = AppointmentRepository(db)

    before_range = create_appointment(
        repository,
        appointment_date=date(2026, 5, 31),
    )
    available = create_appointment(
        repository,
        appointment_date=date(2026, 6, 1),
    )
    occupied = create_appointment(
        repository,
        appointment_date=date(2026, 6, 2),
        status_value="zauzet",
    )

    appointments = repository.get_available(
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 30),
    )

    assert available in appointments
    assert before_range not in appointments
    assert occupied not in appointments

    db.close()


def test_update_appointment_in_database():
    db = TestingSessionLocal()
    repository = AppointmentRepository(db)

    appointment = create_appointment(repository)
    appointment.Status = "zauzet"
    appointment.VrijemeDo = time(10, 30)

    updated_appointment = repository.update(appointment)

    assert updated_appointment.Status == "zauzet"
    assert updated_appointment.VrijemeDo == time(10, 30)

    db.close()


def test_delete_appointment_from_database():
    db = TestingSessionLocal()
    repository = AppointmentRepository(db)

    appointment = create_appointment(repository)
    appointment_id = appointment.IdTermina

    repository.delete(appointment)

    deleted_appointment = repository.get_by_id(appointment_id)

    assert deleted_appointment is None

    db.close()
