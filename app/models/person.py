from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Person(Base):
    __tablename__ = "osoba"

    IdOsobe = Column(Integer, primary_key=True, index=True)

    Ime = Column(String(50), nullable=False)

    Prezime = Column(String(50), nullable=False)

    Email = Column(String(100), nullable=False, unique=True, index=True)

    Telefon = Column(String(30), nullable=True)

    Lozinka = Column(String(255), nullable=False)

    customer_profile = relationship("Customer", back_populates="person", uselist=False)

    employee_profile = relationship("Employee", back_populates="person", uselist=False)


class Customer(Base):
    __tablename__ = "korisnik"

    IdOsobe = Column(Integer, ForeignKey("osoba.IdOsobe", ondelete="CASCADE"), primary_key=True)

    person = relationship("Person", back_populates="customer_profile")

    vehicles = relationship("Vehicle", back_populates="customer")

    reservations = relationship("Reservation", back_populates="customer")

    notifications = relationship("Notification", back_populates="customer")


class Employee(Base):
    __tablename__ = "zaposlenik"

    IdOsobe = Column(Integer, ForeignKey("osoba.IdOsobe", ondelete="CASCADE"), primary_key=True)

    Uloga = Column(String(50), nullable=False, default="serviser")

    person = relationship("Person", back_populates="employee_profile")

    processed_reservations = relationship("Reservation", back_populates="employee")

    processed_appointment_changes = relationship(
        "AppointmentChange",
        back_populates="employee"
    )
