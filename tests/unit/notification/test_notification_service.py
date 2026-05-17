from datetime import date, time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.notification_service import NotificationService


class FakeNotificationRepository:
    def __init__(self):
        self.notifications = []
        self.next_id = 1
        self.updated = []

    def get_by_id(self, notification_id):
        for notification in self.notifications:
            if notification.IdObavijesti == notification_id:
                return notification
        return None

    def get_by_customer_id(self, person_id):
        return [n for n in self.notifications if n.IdOsobe == person_id]

    def get_unread_by_customer_id(self, person_id):
        return [
            n for n in self.notifications
            if n.IdOsobe == person_id and not n.Procitana
        ]

    def create(self, notification):
        notification.IdObavijesti = self.next_id
        self.next_id += 1
        self.notifications.append(notification)
        return notification

    def update(self, notification):
        self.updated.append(notification)
        return notification


class FakeEmailService:
    def __init__(self):
        self.calls = []

    def send(self, recipient, subject, body):
        self.calls.append({
            "recipient": recipient,
            "subject": subject,
            "body": body,
        })
        return True


def _make_service():
    repository = FakeNotificationRepository()
    email_service = FakeEmailService()
    service = NotificationService(repository=repository, email_service=email_service)
    return service, repository, email_service


def _make_reservation(
        reservation_id=1,
        customer_id=100,
        email="korisnik@example.com",
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        reg_oznaka="ZG-123-AB",
        komentar=None,
):
    appointment = SimpleNamespace(Datum=datum, VrijemeOd=vrijeme_od)
    vehicle = SimpleNamespace(RegOznaka=reg_oznaka)
    customer = SimpleNamespace(person=SimpleNamespace(Email=email))
    reservation = SimpleNamespace(
        IdRezervacije=reservation_id,
        IdOsobe_Korisnik=customer_id,
        KomentarZaposlenika=komentar,
        appointment=appointment,
        vehicle=vehicle,
        customer=customer,
    )
    return reservation


def _make_change(
        old_datum=date(2026, 5, 1),
        old_vrijeme=time(9, 0),
        new_datum=date(2026, 5, 5),
        new_vrijeme=time(11, 30),
        reservation=None,
        komentar=None,
):
    if reservation is None:
        reservation = _make_reservation()
    return SimpleNamespace(
        old_appointment=SimpleNamespace(Datum=old_datum, VrijemeOd=old_vrijeme),
        new_appointment=SimpleNamespace(Datum=new_datum, VrijemeOd=new_vrijeme),
        reservation=reservation,
        KomentarZaposlenika=komentar,
    )


def test_notify_reservation_created():
    service, repository, email_service = _make_service()
    reservation = _make_reservation()

    notification = service.notify_reservation_created(reservation)

    assert notification.Naslov == "Rezervacija zaprimljena"
    assert notification.IdOsobe == 100
    assert notification.IdRezervacije == 1
    assert notification.Procitana is False
    assert "01.05.2026." in notification.Tekst
    assert "09:00" in notification.Tekst

    assert len(email_service.calls) == 1
    call = email_service.calls[0]
    assert call["recipient"] == "korisnik@example.com"
    assert call["subject"] == "Rezervacija zaprimljena"
    assert call["body"] == notification.Tekst


def test_notify_reservation_approved_with_comment():
    service, _, email_service = _make_service()
    reservation = _make_reservation(komentar="OK")

    notification = service.notify_reservation_approved(reservation)

    assert notification.Naslov == "Rezervacija odobrena"
    assert "01.05.2026." in notification.Tekst
    assert "09:00" in notification.Tekst
    assert "ZG-123-AB" in notification.Tekst
    assert "Komentar zaposlenika: OK" in notification.Tekst
    assert email_service.calls[0]["subject"] == "Rezervacija odobrena"


def test_notify_reservation_approved_without_comment():
    service, *_ = _make_service()
    reservation = _make_reservation(komentar=None)

    notification = service.notify_reservation_approved(reservation)

    assert "Komentar zaposlenika:" not in notification.Tekst


def test_notify_reservation_rejected_with_comment():
    service, *_ = _make_service()
    reservation = _make_reservation(komentar="Nemamo termina")

    notification = service.notify_reservation_rejected(reservation)

    assert notification.Naslov == "Rezervacija odbijena"
    assert "01.05.2026." in notification.Tekst
    assert "09:00" in notification.Tekst
    assert "Komentar zaposlenika: Nemamo termina" in notification.Tekst


def test_notify_change_requested():
    service, _, email_service = _make_service()
    change = _make_change()

    notification = service.notify_change_requested(change)

    assert notification.Naslov == "Zahtjev za promjenu termina poslan"
    assert "01.05.2026." in notification.Tekst
    assert "09:00" in notification.Tekst
    assert "05.05.2026." in notification.Tekst
    assert "11:30" in notification.Tekst
    assert email_service.calls[0]["subject"] == "Zahtjev za promjenu termina poslan"


def test_notify_change_accepted_with_comment():
    service, *_ = _make_service()
    change = _make_change(komentar="Termin osiguran")

    notification = service.notify_change_accepted(change)

    assert notification.Naslov == "Zahtjev za promjenu termina prihvaćen"
    assert "01.05.2026." in notification.Tekst
    assert "05.05.2026." in notification.Tekst
    assert "Komentar zaposlenika: Termin osiguran" in notification.Tekst


def test_notify_change_rejected_without_comment():
    service, *_ = _make_service()
    change = _make_change(komentar=None)

    notification = service.notify_change_rejected(change)

    assert notification.Naslov == "Zahtjev za promjenu termina odbijen"
    assert "05.05.2026." in notification.Tekst
    assert "11:30" in notification.Tekst
    assert "Komentar zaposlenika:" not in notification.Tekst


def test_mark_as_read_not_found():
    service, *_ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.mark_as_read(notification_id=999, customer_id=100)

    assert error.value.status_code == 404
    assert error.value.detail == "Obavijest nije pronađena."


def test_mark_as_read_forbidden():
    service, repository, _ = _make_service()
    notification = SimpleNamespace(
        IdObavijesti=1,
        IdOsobe=100,
        Procitana=False,
    )
    repository.notifications.append(notification)
    repository.next_id = 2

    with pytest.raises(HTTPException) as error:
        service.mark_as_read(notification_id=1, customer_id=999)

    assert error.value.status_code == 403


def test_mark_as_read_noop_when_already_read():
    service, repository, _ = _make_service()
    notification = SimpleNamespace(
        IdObavijesti=1,
        IdOsobe=100,
        Procitana=True,
    )
    repository.notifications.append(notification)
    repository.next_id = 2

    result = service.mark_as_read(notification_id=1, customer_id=100)

    assert result is notification
    assert result.Procitana is True
    assert repository.updated == []


def test_mark_as_read_success():
    service, repository, _ = _make_service()
    notification = SimpleNamespace(
        IdObavijesti=1,
        IdOsobe=100,
        Procitana=False,
    )
    repository.notifications.append(notification)
    repository.next_id = 2

    result = service.mark_as_read(notification_id=1, customer_id=100)

    assert result.Procitana is True
    assert notification in repository.updated
