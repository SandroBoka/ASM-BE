# ASM-BE

Backend service for the FER Information Systems course project, built with FastAPI, SQLAlchemy, and PostgreSQL.

## Requirements

- Python 3.10 or newer
- `pip`
- Docker with Docker Compose support for the local database stack

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd ASM-BE
```

### 2. Create a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

The application reads configuration from environment variables using `pydantic-settings`.

Create a `.env` file in the project root with:

```env
DATABASE_URL=postgresql://asm_user:asm_password@localhost:5432/asm_db
TEST_DATABASE_URL=postgresql://asm_user:asm_password@localhost:5432/asm_test_db
SECRET_KEY=change-this-to-a-long-random-string
```

If you change the PostgreSQL host port in `docker-compose.yml`, update the port in `DATABASE_URL` and `TEST_DATABASE_URL` to match.
`TEST_DATABASE_URL` is used by repository, route, and integration tests that touch the database.

Authentication settings are also loaded from `.env`. `SECRET_KEY` is required and is used to sign JWT access tokens. The following values have defaults in `app/core/config.py`, but can be overridden from `.env` if needed:

```env
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=14
```

Generate a stronger local development secret with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### SMTP (E-mail notifications)

The `NotificationService` sends real e-mails through Gmail SMTP when reservations or appointment-change requests are processed. Add the following to `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=asm.servis.demo@gmail.com
SMTP_PASSWORD=<internally shared>
```

`SMTP_HOST` and `SMTP_PORT` have defaults in `app/core/config.py` and may be omitted. `SMTP_USER` and `SMTP_PASSWORD` are required.

`SMTP_PASSWORD` is a 16-character Gmail **App Password**, not the regular account password. The demo project shares a dedicated account (`asm.servis.demo@gmail.com`); the App Password is shared with the team out-of-band (not committed). To use a different Gmail account:

1. Enable 2-Step Verification on the account: <https://myaccount.google.com/security>
2. Generate an App Password: <https://myaccount.google.com/apppasswords>
3. Paste the 16-character value into `SMTP_PASSWORD` (spaces are optional).

## Running the Database Stack

The project includes a Docker Compose setup for PostgreSQL and Adminer.

Start the services:

```bash
docker compose up -d
```

Stop the services:

```bash
docker compose down
```

### Included Services

#### PostgreSQL

- image: `postgres:16`
- container name: `asm_postgres`
- host port: `5432`
- container port: `5432`
- database: `asm_db`
- username: `asm_user`
- password: `asm_password`

#### Adminer

- image: `adminer:latest`
- container name: `asm_adminer`
- host URL: `http://127.0.0.1:8081`
- container port: `8080`

### Adminer Login Values

- System: `PostgreSQL`
- Server: `db`
- Username: `asm_user`
- Password: `asm_password`
- Database: `asm_db`

### Port Note

If port `5432` is already in use on your machine, change the PostgreSQL mapping in [docker-compose.yml](/Users/sandro/Documents/FER/8_semestar/INFSUS/ASM-BE/docker-compose.yml:1) from:

```yaml
ports:
  - "5432:5432"
```

to:

```yaml
ports:
  - "5433:5432"
```

Then update `.env` accordingly:

```env
DATABASE_URL=postgresql://asm_user:asm_password@localhost:5433/asm_db
TEST_DATABASE_URL=postgresql://asm_user:asm_password@localhost:5433/asm_test_db
```

## Database Migrations

The project uses Alembic for schema migrations.

Apply the latest migrations after starting PostgreSQL:

```bash
alembic upgrade head
```

The migrations create the service catalog table and the current core ASM schema:

- `usluga`: service catalog
- `osoba`: shared person data and credentials
- `korisnik`: customer profile linked one-to-one to `osoba`
- `zaposlenik`: employee profile linked one-to-one to `osoba`
- `refresh_token`: hashed refresh tokens used for session renewal and logout
- `vozilo`: customer vehicles
- `termin`: appointment slots
- `rezervacija`: service reservations
- `promjena_termina`: appointment change requests
- `rezervacija_usluga`: reservation-service join table
- `obavijest`: customer notifications

The HTTP API exposes flows for authentication, the service catalog, persons/customers/employees, vehicles, appointments, reservations, appointment-change requests, and customer notifications.

## Running the Application

Start the FastAPI development server with:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`

## API Documentation

FastAPI generates interactive documentation automatically:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Implemented Endpoints

Most application routes require a JWT access token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

Public routes:

- `GET /health`
- `GET /db-check`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /persons/customers`

`/auth/refresh` and `/auth/logout` do not require an access token because they operate on the refresh token in the request body. All other application routes require an access token, except `POST /persons/customers`, which is public customer registration.

The API currently distinguishes authenticated users by:

- `TipKorisnika`: `customer` or `employee`
- `Uloga`: employee role, currently `admin`, `serviser`, or `voditelj`; customers have `Uloga: null`

Admin users are employees with `Uloga: "admin"`.

### Health and Database Checks

- `GET /health`
- `GET /db-check`

### Authentication

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

Login request:

```json
{
  "Email": "ivan@example.com",
  "Lozinka": "tajna123"
}
```

Login and refresh response:

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "plain-refresh-token",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "IdOsobe": 1,
    "Ime": "Ivan",
    "Prezime": "Horvat",
    "Email": "ivan@example.com",
    "TipKorisnika": "customer",
    "Uloga": null
  }
}
```

Refresh and logout request:

```json
{
  "refresh_token": "plain-refresh-token"
}
```

Access tokens are JWTs valid for 24 hours by default. Refresh tokens are random tokens valid for 14 days by default. The API stores only a SHA-256 hash of each refresh token in the `refresh_token` table. Refreshing rotates the refresh token: the old one is revoked and a new one is issued. Logout revokes the provided refresh token.

### Services

- `GET /services`
- `GET /services?search=<text>`
- `GET /services/{service_id}`
- `POST /services`
- `PUT /services/{service_id}`
- `DELETE /services/{service_id}`

All authenticated users can list and view services. Creating, updating, and deleting services requires an employee account. Customers can read the service catalog, but cannot modify it.

Service request fields:

- `NazivUsluge`: required service name
- `Opis`: optional service description
- `Trajanje`: duration in minutes, must be greater than 0
- `Cijena`: price, cannot be negative

### Persons, Customers, and Employees

- `GET /persons`
- `GET /persons/{person_id}`
- `PUT /persons/{person_id}`
- `DELETE /persons/{person_id}`
- `GET /persons/customers/{customer_id}`
- `POST /persons/customers`
- `PUT /persons/customers/{customer_id}`
- `GET /persons/employees/{employee_id}`
- `POST /persons/employees`
- `PUT /persons/employees/{employee_id}`
- `PATCH /persons/employees/{employee_id}/role`

Person request fields:

- `Ime`: required first name
- `Prezime`: required last name
- `Email`: required unique email address
- `Telefon`: optional phone number
- `Lozinka`: required password on create and optional on update

Employee request fields additionally support:

- `Uloga`: employee role, defaulting to `serviser` on create; accepted values are `admin`, `serviser`, and `voditelj`

Password values are hashed before they are stored, and response models do not return `Lozinka`.

Customer registration through `POST /persons/customers` is public. All other person/customer/employee routes require an access token.

Current access rules:

- employees can list and view persons, customers, and employees
- customers can view and update their own customer profile
- customers can delete their own account
- only admins can create employees
- only admins can update generic person records through `PUT /persons/{person_id}`
- only admins can change employee roles through `PATCH /persons/employees/{employee_id}/role`
- admins can update or delete any person; non-admin users are restricted to self-owned profile operations where supported

### Vehicles

- `GET /vehicles/customers/{customer_id}`
- `GET /vehicles/{vehicle_id}`
- `POST /vehicles`
- `PUT /vehicles/{vehicle_id}`
- `DELETE /vehicles/{vehicle_id}`

Vehicle request fields:

- `Marka`: required vehicle make
- `Model`: required vehicle model
- `Godina`: vehicle year, must be between 1900 and 2100
- `VrstaMotora`: required engine type
- `RegOznaka`: required unique registration plate
- `IdOsobe`: customer ID, required when creating a vehicle

Vehicles belong to customers through `IdOsobe`. Registration plates must be unique.

All vehicle routes require an access token. Access is guarded by vehicle ownership:

- employees can list and view customer vehicles
- customers can list and view only their own vehicles
- admins can create vehicles for any customer
- customers can create vehicles only for their own customer profile
- admins can update or delete any vehicle
- customers can update or delete only their own vehicles

Deleting a customer also deletes that customer's vehicles through ORM cascade behavior and database foreign-key cascade rules.

### Appointments

- `GET /appointments/free`
- `GET /appointments/free?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
- `GET /appointments`
- `GET /appointments/{appointment_id}`
- `POST /appointments`
- `PUT /appointments/{appointment_id}`
- `DELETE /appointments/{appointment_id}`

Appointment request fields:

- `Datum`: appointment date
- `VrijemeOd`: start time
- `VrijemeDo`: end time, must be after `VrijemeOd`
- `Status`: accepted values are `slobodan`, `zauzet`, and `otkazan`; defaults to `slobodan`

Access rules:

- any authenticated user can view a single appointment and list free appointments
- employees can list all appointments
- only admins and workshop leads (`voditelj`) can create, update, or delete appointments
- occupied appointments, or appointments already linked to reservations or appointment-change requests, cannot be deleted

### Reservations

- `GET /reservations`
- `GET /reservations/pending`
- `GET /reservations/customer/{customer_id}`
- `GET /reservations/{reservation_id}`
- `POST /reservations`
- `PUT /reservations/{reservation_id}`
- `POST /reservations/{reservation_id}/services`
- `PUT /reservations/{reservation_id}/services/{service_id}`
- `DELETE /reservations/{reservation_id}/services/{service_id}`
- `POST /reservations/{reservation_id}/approve`
- `POST /reservations/{reservation_id}/reject`
- `POST /reservations/{reservation_id}/cancel`
- `POST /reservations/{reservation_id}/complete`

Reservation creation request:

```json
{
  "IdOsobe_Korisnik": 1,
  "IdTermina": 1,
  "IdVozila": 1,
  "KilometrazaVozila": 50000,
  "OpisProblema": "Cudan zvuk pri paljenju",
  "services": [
    {
      "IdUsluge": 1,
      "Kolicina": 1
    }
  ]
}
```

Reservation rules:

- `KilometrazaVozila` cannot be negative
- `OpisProblema` is required
- each reservation must contain at least one service
- service quantity must be at least 1
- the selected vehicle must belong to the customer
- the selected appointment must be free
- the total service duration must fit into the selected appointment slot when editing reservation services

Reservation statuses are:

- `na cekanju`
- `odobrena`
- `odbijena`
- `otkazana`
- `zavrsena`

Allowed status transitions:

- `na cekanju` -> `odobrena`, `odbijena`, `otkazana`
- `odobrena` -> `otkazana`, `zavrsena`

Access rules:

- customers can create and edit their own pending reservations
- employees can list all reservations and all pending reservations
- employees can view reservations for any customer
- customers can view only their own reservations
- approving and rejecting reservations requires an employee account
- canceling is allowed for the owning customer or an admin
- completing a reservation requires an employee account

Reservation actions send customer notifications by e-mail and persist them in `obavijest`.

### Appointment Changes

- `GET /appointment-changes`
- `GET /appointment-changes/pending`
- `GET /appointment-changes/reservation/{reservation_id}`
- `GET /appointment-changes/{change_id}`
- `POST /appointment-changes`
- `POST /appointment-changes/{change_id}/accept`
- `POST /appointment-changes/{change_id}/reject`

Appointment-change request:

```json
{
  "IdRezervacije": 1,
  "IdNovogTermina": 2
}
```

Accept/reject request:

```json
{
  "komentar": "Termin je potvrden"
}
```

Appointment-change rules:

- changes can be requested only for approved reservations
- the new appointment must be different from the current appointment
- the new appointment must be free
- accepting a change frees the old appointment, occupies the new appointment, and moves the reservation to the new appointment
- rejecting a change leaves the reservation and appointments unchanged

Appointment-change statuses are:

- `na cekanju`
- `prihvacen`
- `odbijen`

Access rules:

- customers can request changes only for their own reservations
- employees can list and process pending change requests
- customers can view change requests for their own reservations
- employees can view change requests for any reservation

### Notifications

- `GET /notifications`
- `GET /notifications/unread`
- `POST /notifications/{notification_id}/read`

Notifications are created when reservations and appointment-change requests are created, approved, rejected, or canceled. They are stored in the database and also sent through the configured e-mail service.

Access rules:

- notification routes are customer-only
- customers can list their own notifications
- customers can list only their unread notifications
- customers can mark only their own notifications as read

## Module Overview

### `app/`

- contains the FastAPI application entry point and application modules

### `app/api/routes/`

- contains FastAPI route definitions
- groups HTTP endpoints by feature, such as health checks, database checks, authentication, service catalog operations, person operations, vehicle operations, appointment scheduling, reservations, appointment-change requests, and notifications

### `app/api/dependencies/`

- contains reusable FastAPI dependencies
- provides auth helpers for reading bearer tokens, loading the current user, and enforcing customer/employee/admin/self access rules

### `app/core/`

- contains application configuration
- loads environment-based settings from `.env`
- defines shared auth enum values for user types and employee roles

### `app/db/`

- contains database setup
- exposes the SQLAlchemy engine, session factory, declarative base, and database dependency

### `app/models/`

- contains SQLAlchemy ORM models
- maps Python classes to database tables

### `app/repositories/`

- contains database access logic
- handles queries, inserts, updates, deletes, and persistence concerns

### `app/schemas/`

- contains Pydantic models
- defines request and response shapes used by the API

### `app/services/`

- contains business logic
- validates input and coordinates repository operations

### `alembic/`

- contains Alembic migration configuration and migration scripts

### `tests/`

- contains unit tests for route behavior, repository persistence, and service-layer validation
- contains unit test coverage for auth, services, persons, vehicles, appointments, reservations, appointment changes, and notifications
- contains integration tests for auth, service, person, vehicle, and reservation API flows

### `docker-compose.yml`

- defines the local PostgreSQL service
- defines the Adminer service for database inspection
- creates the named Docker volume `asm_postgres_data` for persistent database storage

## Running Tests

Run the full test suite with:

```bash
pytest
```

Database-backed tests use `TEST_DATABASE_URL`. Create the test database before running them, for example through Adminer or `psql`:

```sql
CREATE DATABASE asm_test_db;
```

The database-backed tests call `drop_all` and `create_all` on the test database. Do not run multiple pytest processes in parallel against the same `asm_test_db`, because concurrent table drops and creates can race each other.

Some route tests override the notification e-mail dependency with a fake mail service so the test suite does not send real SMTP messages.

## Common Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the database services:

```bash
docker compose up -d
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Apply database migrations:

```bash
alembic upgrade head
```

Check the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Check the database connection:

```bash
curl http://127.0.0.1:8000/db-check
```

Run tests:

```bash
pytest
```

Stop the database services:

```bash
docker compose down
```
