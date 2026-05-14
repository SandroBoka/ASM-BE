from enum import Enum


class EmployeeRole(str, Enum):
    ADMIN = "admin"
    SERVISER = "serviser"
    VODITELJ = "voditelj"


class UserType(str, Enum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
