from fastapi import HTTPException, status

from app.models.appointment_change import AppointmentChange
from app.models.notification import Notification
from app.models.reservation import Reservation
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import EmailService


SIGNATURE = "— ASM Servis"


class NotificationService:
    def __init__(
            self,
            repository: NotificationRepository,
            email_service: EmailService,
    ):
        self.repository = repository
        self.email_service = email_service

    def notify_reservation_created(self, reservation: Reservation) -> Notification:
        naslov = "Rezervacija zaprimljena"
        tekst = self._format_created_text(reservation)
        return self._send_and_save(reservation, naslov, tekst)

    def notify_reservation_approved(self, reservation: Reservation) -> Notification:
        naslov = "Rezervacija odobrena"
        tekst = self._format_approved_text(reservation)
        return self._send_and_save(reservation, naslov, tekst)

    def notify_reservation_rejected(self, reservation: Reservation) -> Notification:
        naslov = "Rezervacija odbijena"
        tekst = self._format_rejected_text(reservation)
        return self._send_and_save(reservation, naslov, tekst)

    def notify_reservation_canceled(self, reservation: Reservation) -> Notification:
        naslov = "Rezervacija otkazana"
        tekst = self._format_canceled_text(reservation)
        return self._send_and_save(reservation, naslov, tekst)

    def notify_change_requested(self, change: AppointmentChange) -> Notification:
        naslov = "Zahtjev za promjenu termina poslan"
        tekst = self._format_change_requested_text(change)
        return self._send_and_save(change.reservation, naslov, tekst)

    def notify_change_accepted(self, change: AppointmentChange) -> Notification:
        naslov = "Zahtjev za promjenu termina prihvaćen"
        tekst = self._format_change_accepted_text(change)
        return self._send_and_save(change.reservation, naslov, tekst)

    def notify_change_rejected(self, change: AppointmentChange) -> Notification:
        naslov = "Zahtjev za promjenu termina odbijen"
        tekst = self._format_change_rejected_text(change)
        return self._send_and_save(change.reservation, naslov, tekst)

    def get_notifications_for_customer(self, customer_id: int) -> list[Notification]:
        return self.repository.get_by_customer_id(customer_id)

    def get_unread_for_customer(self, customer_id: int) -> list[Notification]:
        return self.repository.get_unread_by_customer_id(customer_id)

    def mark_as_read(self, notification_id: int, customer_id: int) -> Notification:
        notification = self.repository.get_by_id(notification_id)

        if notification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Obavijest nije pronađena."
            )

        if notification.IdOsobe != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Možete označiti samo vlastite obavijesti kao pročitane."
            )

        if notification.Procitana:
            return notification

        notification.Procitana = True
        return self.repository.update(notification)

    def _send_and_save(
            self,
            reservation: Reservation,
            naslov: str,
            tekst: str,
    ) -> Notification:
        notification = Notification(
            Naslov=naslov,
            Tekst=tekst,
            IdOsobe=reservation.IdOsobe_Korisnik,
            IdRezervacije=reservation.IdRezervacije,
            Procitana=False,
        )
        saved = self.repository.create(notification)

        recipient_email = reservation.customer.person.Email
        self.email_service.send(
            recipient=recipient_email,
            subject=naslov,
            body=f"{tekst}\n\n{SIGNATURE}",
        )

        return saved

    @staticmethod
    def _format_created_text(reservation: Reservation) -> str:
        datum = reservation.appointment.Datum.strftime("%d.%m.%Y.")
        vrijeme = reservation.appointment.VrijemeOd.strftime("%H:%M")
        return (
            f"Vaša rezervacija za {datum} u {vrijeme} je zaprimljena "
            f"i čeka obradu zaposlenika."
        )

    @staticmethod
    def _format_approved_text(reservation: Reservation) -> str:
        datum = reservation.appointment.Datum.strftime("%d.%m.%Y.")
        vrijeme = reservation.appointment.VrijemeOd.strftime("%H:%M")
        reg_oznaka = reservation.vehicle.RegOznaka

        lines = [
            f"Vaša rezervacija za {datum} u {vrijeme} je odobrena.",
            f"Očekujemo Vas s vozilom {reg_oznaka}.",
        ]

        if reservation.KomentarZaposlenika:
            lines.append("")
            lines.append(f"Komentar zaposlenika: {reservation.KomentarZaposlenika}")

        return "\n".join(lines)

    @staticmethod
    def _format_rejected_text(reservation: Reservation) -> str:
        datum = reservation.appointment.Datum.strftime("%d.%m.%Y.")
        vrijeme = reservation.appointment.VrijemeOd.strftime("%H:%M")

        lines = [
            f"Vaša rezervacija za {datum} u {vrijeme} je odbijena.",
        ]

        if reservation.KomentarZaposlenika:
            lines.append("")
            lines.append(f"Komentar zaposlenika: {reservation.KomentarZaposlenika}")

        return "\n".join(lines)

    @staticmethod
    def _format_canceled_text(reservation: Reservation) -> str:
        datum = reservation.appointment.Datum.strftime("%d.%m.%Y.")
        vrijeme = reservation.appointment.VrijemeOd.strftime("%H:%M")

        lines = [
            f"Vaša rezervacija za {datum} u {vrijeme} je otkazana.",
        ]

        if reservation.KomentarZaposlenika:
            lines.append("")
            lines.append(f"Komentar: {reservation.KomentarZaposlenika}")

        return "\n".join(lines)

    @staticmethod
    def _format_change_requested_text(change: AppointmentChange) -> str:
        old_datum = change.old_appointment.Datum.strftime("%d.%m.%Y.")
        old_vrijeme = change.old_appointment.VrijemeOd.strftime("%H:%M")
        new_datum = change.new_appointment.Datum.strftime("%d.%m.%Y.")
        new_vrijeme = change.new_appointment.VrijemeOd.strftime("%H:%M")

        return (
            "Vaš zahtjev za promjenu termina je zaprimljen i čeka obradu.\n"
            f"Stari termin: {old_datum} u {old_vrijeme}\n"
            f"Predloženi novi termin: {new_datum} u {new_vrijeme}"
        )

    @staticmethod
    def _format_change_accepted_text(change: AppointmentChange) -> str:
        old_datum = change.old_appointment.Datum.strftime("%d.%m.%Y.")
        old_vrijeme = change.old_appointment.VrijemeOd.strftime("%H:%M")
        new_datum = change.new_appointment.Datum.strftime("%d.%m.%Y.")
        new_vrijeme = change.new_appointment.VrijemeOd.strftime("%H:%M")

        lines = [
            "Vaš zahtjev za promjenu termina je prihvaćen.",
            f"Stari termin: {old_datum} u {old_vrijeme}",
            f"Novi termin: {new_datum} u {new_vrijeme}",
        ]

        if change.KomentarZaposlenika:
            lines.append("")
            lines.append(f"Komentar zaposlenika: {change.KomentarZaposlenika}")

        return "\n".join(lines)

    @staticmethod
    def _format_change_rejected_text(change: AppointmentChange) -> str:
        new_datum = change.new_appointment.Datum.strftime("%d.%m.%Y.")
        new_vrijeme = change.new_appointment.VrijemeOd.strftime("%H:%M")

        lines = [
            "Vaš zahtjev za promjenu termina je odbijen.",
            f"Predloženi novi termin bio je: {new_datum} u {new_vrijeme}",
        ]

        if change.KomentarZaposlenika:
            lines.append("")
            lines.append(f"Komentar zaposlenika: {change.KomentarZaposlenika}")

        return "\n".join(lines)
