from enum import Enum


class AppointmentStatus(str, Enum):
    SLOBODAN = "slobodan"
    ZAUZET = "zauzet"
    OTKAZAN = "otkazan"


class ReservationStatus(str, Enum):
    NA_CEKANJU = "na cekanju"
    ODOBRENA = "odobrena"
    ODBIJENA = "odbijena"
    OTKAZANA = "otkazana"
    ZAVRSENA = "zavrsena"


class AppointmentChangeStatus(str, Enum):
    NA_CEKANJU = "na cekanju"
    PRIHVACEN = "prihvacen"
    ODBIJEN = "odbijen"
