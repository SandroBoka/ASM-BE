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
```

If you change the PostgreSQL host port in [docker-compose.yml](/Users/sandro/Documents/FER/8_semestar/INFSUS/ASM-BE/docker-compose.yml:1), update the port in `DATABASE_URL` to match.
`TEST_DATABASE_URL` is used by the integration test suite.

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

The current migration creates the `usluga` table used by the service catalog:

- `IdUsluge`: primary key
- `NazivUsluge`: required service name, up to 100 characters
- `Opis`: optional service description
- `Trajanje`: required service duration in minutes
- `Cijena`: required service price with two decimal places

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

## Module Overview

### `app/`

- contains the FastAPI application entry point and application modules

### `app/api/routes/`

- contains FastAPI route definitions
- groups HTTP endpoints by feature, such as health checks, database checks, and service catalog operations

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

- contains unit tests for routes, repository behavior, and service-layer validation
- contains an integration test for the full service CRUD flow

### `docker-compose.yml`

- defines the local PostgreSQL service
- defines the Adminer service for database inspection
- creates the named Docker volume `asm_postgres_data` for persistent database storage

## Running Tests

Run the full test suite with:

```bash
pytest
```

Integration tests use `TEST_DATABASE_URL`. Create the test database before running them, for example through Adminer or `psql`:

```sql
CREATE DATABASE asm_test_db;
```

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

List services:

```bash
curl http://127.0.0.1:8000/services
```

Run tests:

```bash
pytest
```

Stop the database services:

```bash
docker compose down
```
