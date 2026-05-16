from enum import Enum


class AppointmentStatus(str, Enum):
    SLOBODAN = "slobodan"
    ZAUZET = "zauzet"
    OTKAZAN = "otkazan"
