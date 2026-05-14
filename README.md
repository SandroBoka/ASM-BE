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

The auth, service catalog, person/customer/employee, and vehicle API modules are currently exposed through HTTP routes.

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

`/auth/refresh` and `/auth/logout` do not require an access token because they operate on the refresh token in the request body. All service routes, vehicle routes, `/auth/me`, and all person routes except customer registration require an access token.

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

- `Uloga`: employee role, defaulting to `serviser` on create

Password values are hashed before they are stored, and response models do not return `Lozinka`.

Customer registration through `POST /persons/customers` is public. All other person/customer/employee routes require an access token.

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

All vehicle routes require an access token. Deleting a customer also deletes that customer's vehicles through ORM cascade behavior and database foreign-key cascade rules.

## Module Overview

### `app/`

- contains the FastAPI application entry point and application modules

### `app/api/routes/`

- contains FastAPI route definitions
- groups HTTP endpoints by feature, such as health checks, database checks, authentication, service catalog operations, person operations, and vehicle operations

### `app/api/dependencies/`

- contains reusable FastAPI dependencies
- provides auth helpers for reading bearer tokens, loading the current user, and enforcing customer/employee/role-based access

### `app/core/`

- contains application configuration
- loads environment-based settings from `.env`

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
- contains integration tests for auth, service, person, and vehicle API flows

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
