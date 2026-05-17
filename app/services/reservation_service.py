from fastapi import HTTPException, status

from app.core.statuses import AppointmentStatus, ReservationStatus
from app.models.reservation import Reservation
from app.models.reservation_service import ReservationService as ReservationServiceLink
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.reservation_schema import ReservationServiceItemCreate
from app.services.appointment_service import AppointmentService
from app.services.service_catalog_service import ServiceCatalogService
from app.services.vehicle_service import VehicleService


class ReservationService:
    ALLOWED_TRANSITIONS: dict[ReservationStatus, set[ReservationStatus]] = {
        ReservationStatus.NA_CEKANJU: {
            ReservationStatus.ODOBRENA,
            ReservationStatus.ODBIJENA,
            ReservationStatus.OTKAZANA,
        },
        ReservationStatus.ODOBRENA: {
            ReservationStatus.OTKAZANA,
            ReservationStatus.ZAVRSENA,
        },
    }

    def __init__(
            self,
            repository: ReservationRepository,
            appointment_service: AppointmentService,
            vehicle_service: VehicleService,
            service_catalog_service: ServiceCatalogService,
    ):
        self.repository = repository
        self.appointment_service = appointment_service
        self.vehicle_service = vehicle_service
        self.service_catalog_service = service_catalog_service

    def get_all_reservations(self) -> list[Reservation]:
        return self.repository.get_all()

    def get_pending_reservations(self) -> list[Reservation]:
        return self.repository.get_by_status(ReservationStatus.NA_CEKANJU.value)

    def get_reservation_by_id(self, reservation_id: int) -> Reservation:
        reservation = self.repository.get_by_id(reservation_id)

        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezervacija nije pronađena."
            )

        return reservation

    def get_reservations_by_customer_id(self, person_id: int) -> list[Reservation]:
        return self.repository.get_by_customer_id(person_id)

    def create_reservation(
            self,
            id_osobe_korisnik: int,
            id_termina: int,
            id_vozila: int,
            kilometraza_vozila: int,
            opis_problema: str,
            services: list[ReservationServiceItemCreate]
    ) -> Reservation:
        self._validate_create_data(
            kilometraza_vozila=kilometraza_vozila,
            opis_problema=opis_problema,
            services=services
        )

        vehicle = self.vehicle_service.get_vehicle_by_id(id_vozila)
        if vehicle.IdOsobe != id_osobe_korisnik:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odabrano vozilo ne pripada korisniku."
            )

        for item in services:
            self.service_catalog_service.get_service_by_id(item.IdUsluge)

        appointment = self.appointment_service.get_appointment_by_id(id_termina)
        if appointment.Status != AppointmentStatus.SLOBODAN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Termin nije slobodan. Odaberite drugi termin."
            )

        reservation = Reservation(
            Status=ReservationStatus.NA_CEKANJU.value,
            KilometrazaVozila=kilometraza_vozila,
            OpisProblema=opis_problema.strip(),
            IdOsobe_Korisnik=id_osobe_korisnik,
            IdTermina=id_termina,
            IdVozila=id_vozila,
        )
        created = self.repository.create(reservation)

        for item in services:
            link = ReservationServiceLink(
                IdRezervacije=created.IdRezervacije,
                IdUsluge=item.IdUsluge,
                Kolicina=item.Kolicina,
            )
            self.repository.add_service(link)

        self.repository.db.refresh(created)
        return created

    def update_reservation_header(
            self,
            reservation_id: int,
            id_osobe_korisnik: int,
            id_termina: int,
            id_vozila: int,
            kilometraza_vozila: int,
            opis_problema: str,
    ) -> Reservation:
        reservation = self._get_editable_reservation(reservation_id, id_osobe_korisnik)

        if kilometraza_vozila < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kilometraža vozila ne smije biti negativna.",
            )
        if not opis_problema or not opis_problema.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opis problema je obavezno polje.",
            )

        vehicle = self.vehicle_service.get_vehicle_by_id(id_vozila)
        if vehicle.IdOsobe != id_osobe_korisnik:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odabrano vozilo ne pripada korisniku.",
            )

        if id_termina != reservation.IdTermina:
            appointment = self.appointment_service.get_appointment_by_id(id_termina)
            if appointment.Status != AppointmentStatus.SLOBODAN:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Odabrani termin nije slobodan.",
                )

        reservation.IdTermina = id_termina
        reservation.IdVozila = id_vozila
        reservation.KilometrazaVozila = kilometraza_vozila
        reservation.OpisProblema = opis_problema.strip()
        return self.repository.update(reservation)

    def add_service_to_reservation(
            self,
            reservation_id: int,
            id_osobe_korisnik: int,
            id_usluge: int,
            kolicina: int,
    ) -> ReservationServiceLink:
        reservation = self._get_editable_reservation(reservation_id, id_osobe_korisnik)

        if kolicina < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Količina mora biti najmanje 1.",
            )

        self.service_catalog_service.get_service_by_id(id_usluge)

        if self.repository.get_service_link(reservation_id, id_usluge) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ova usluga je već dodana u rezervaciju. Uredi količinu umjesto dodavanja.",
            )

        self._check_slot_capacity(
            reservation,
            extra_service_id=id_usluge,
            extra_kolicina=kolicina,
        )

        link = ReservationServiceLink(
            IdRezervacije=reservation_id,
            IdUsluge=id_usluge,
            Kolicina=kolicina,
        )
        return self.repository.add_service(link)

    def update_service_quantity(
            self,
            reservation_id: int,
            id_osobe_korisnik: int,
            id_usluge: int,
            kolicina: int,
    ) -> ReservationServiceLink:
        reservation = self._get_editable_reservation(reservation_id, id_osobe_korisnik)

        if kolicina < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Količina mora biti najmanje 1.",
            )

        link = self.repository.get_service_link(reservation_id, id_usluge)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usluga nije pronađena u rezervaciji.",
            )

        self._check_slot_capacity(
            reservation,
            replace_service_id=id_usluge,
            replace_kolicina=kolicina,
        )

        link.Kolicina = kolicina
        return self.repository.update_service_link(link)

    def remove_service_from_reservation(
            self,
            reservation_id: int,
            id_osobe_korisnik: int,
            id_usluge: int,
    ) -> None:
        reservation = self._get_editable_reservation(reservation_id, id_osobe_korisnik)

        link = self.repository.get_service_link(reservation_id, id_usluge)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usluga nije pronađena u rezervaciji.",
            )

        if len(reservation.reservation_services) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Rezervacija mora sadržavati barem jednu uslugu.",
            )

        self.repository.delete_service_link(link)

    def _get_editable_reservation(
            self,
            reservation_id: int,
            id_osobe_korisnik: int,
    ) -> Reservation:
        reservation = self.get_reservation_by_id(reservation_id)

        if reservation.IdOsobe_Korisnik != id_osobe_korisnik:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Možete uređivati samo vlastite rezervacije.",
            )

        if reservation.Status != ReservationStatus.NA_CEKANJU:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Uređivanje je moguće samo dok je rezervacija u statusu 'na cekanju'.",
            )

        return reservation

    def _check_slot_capacity(
            self,
            reservation: Reservation,
            extra_service_id: int | None = None,
            extra_kolicina: int = 0,
            replace_service_id: int | None = None,
            replace_kolicina: int = 0,
    ) -> None:
        appointment = self.appointment_service.get_appointment_by_id(reservation.IdTermina)
        slot_minutes = (
            appointment.VrijemeDo.hour * 60 + appointment.VrijemeDo.minute
        ) - (appointment.VrijemeOd.hour * 60 + appointment.VrijemeOd.minute)

        total = 0
        for link in reservation.reservation_services:
            service = self.service_catalog_service.get_service_by_id(link.IdUsluge)
            kolicina = link.Kolicina
            if replace_service_id is not None and link.IdUsluge == replace_service_id:
                kolicina = replace_kolicina
            total += service.Trajanje * kolicina

        if extra_service_id is not None:
            service = self.service_catalog_service.get_service_by_id(extra_service_id)
            total += service.Trajanje * extra_kolicina

        if total > slot_minutes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Ukupno trajanje usluga ({total} min) ne stane u termin "
                    f"({slot_minutes} min)."
                ),
            )

    def approve_reservation(
            self,
            reservation_id: int,
            id_osobe_zaposlenik: int,
            komentar: str | None = None,
    ) -> Reservation:
        reservation = self.get_reservation_by_id(reservation_id)
        self._validate_transition(reservation.Status, ReservationStatus.ODOBRENA)

        appointment = self.appointment_service.get_appointment_by_id(reservation.IdTermina)
        if appointment.Status != AppointmentStatus.SLOBODAN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Termin više nije slobodan. Zahtjev je potrebno odbiti."
            )

        existing_approved = self.repository.get_approved_by_appointment_id(reservation.IdTermina)
        if existing_approved is not None and existing_approved.IdRezervacije != reservation_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Za ovaj termin već postoji odobrena rezervacija."
            )

        self.appointment_service.mark_as_occupied(reservation.IdTermina)

        reservation.Status = ReservationStatus.ODOBRENA.value
        reservation.IdOsobe_Zaposlenik = id_osobe_zaposlenik
        if komentar is not None:
            reservation.KomentarZaposlenika = komentar.strip() or None

        return self.repository.update(reservation)

    def reject_reservation(
            self,
            reservation_id: int,
            id_osobe_zaposlenik: int,
            komentar: str | None = None,
    ) -> Reservation:
        reservation = self.get_reservation_by_id(reservation_id)
        self._validate_transition(reservation.Status, ReservationStatus.ODBIJENA)

        reservation.Status = ReservationStatus.ODBIJENA.value
        reservation.IdOsobe_Zaposlenik = id_osobe_zaposlenik
        if komentar is not None:
            reservation.KomentarZaposlenika = komentar.strip() or None

        return self.repository.update(reservation)

    def cancel_reservation(
            self,
            reservation_id: int,
            komentar: str | None = None,
    ) -> Reservation:
        reservation = self.get_reservation_by_id(reservation_id)
        self._validate_transition(reservation.Status, ReservationStatus.OTKAZANA)

        was_approved = reservation.Status == ReservationStatus.ODOBRENA

        reservation.Status = ReservationStatus.OTKAZANA.value
        if komentar is not None:
            reservation.KomentarZaposlenika = komentar.strip() or None

        updated = self.repository.update(reservation)

        if was_approved:
            self.appointment_service.mark_as_free(reservation.IdTermina)

        return updated

    def complete_reservation(self, reservation_id: int) -> Reservation:
        reservation = self.get_reservation_by_id(reservation_id)
        self._validate_transition(reservation.Status, ReservationStatus.ZAVRSENA)

        reservation.Status = ReservationStatus.ZAVRSENA.value
        return self.repository.update(reservation)

    def _validate_create_data(
            self,
            kilometraza_vozila: int,
            opis_problema: str,
            services: list[ReservationServiceItemCreate]
    ) -> None:
        if kilometraza_vozila < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kilometraža vozila ne smije biti negativna."
            )

        if not opis_problema or not opis_problema.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opis problema je obavezno polje."
            )

        if not services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odaberite barem jednu uslugu."
            )

        for item in services:
            if item.Kolicina < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Količina usluge mora biti najmanje 1."
                )

    def _validate_transition(
            self,
            current_status: str,
            target_status: ReservationStatus,
    ) -> None:
        try:
            current = ReservationStatus(current_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nepoznat trenutni status rezervacije: {current_status!r}."
            )

        allowed = self.ALLOWED_TRANSITIONS.get(current, set())
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Tranzicija statusa rezervacije iz '{current.value}' "
                    f"u '{target_status.value}' nije dozvoljena."
                )
            )
