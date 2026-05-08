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
```

If you change the PostgreSQL host port in [docker-compose.yml](/Users/sandro/Documents/FER/8_semestar/INFSUS/ASM-BE/docker-compose.yml:1), update the port in `DATABASE_URL` to match.

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
```

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

## Available Endpoints

### `GET /health`

Returns a simple service health response.

Example request:

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{
  "status": "ok",
  "service": "ASM Backend"
}
```

### `GET /db-check`

Checks database connectivity by opening a SQLAlchemy connection and running `SELECT 1`.

Example request:

```bash
curl http://127.0.0.1:8000/db-check
```

Example response:

```json
{
  "database_connected": true
}
```

## Project Structure

```text
ASM-BE/
├── docker-compose.yml
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── db_routes.py
│   │       └── health_routes.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── repositories/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── health_service.py
│   ├── __init__.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Module Overview

### `app/main.py`

- creates the FastAPI application
- registers API routers

### `app/api/routes/health_routes.py`

- defines the `/health` endpoint

### `app/api/routes/db_routes.py`

- defines the `/db-check` endpoint
- uses the shared SQLAlchemy engine to test database connectivity

### `app/core/config.py`

- loads application settings from `.env`
- exposes `DATABASE_URL` through the `settings` object

### `app/db/database.py`

- creates the SQLAlchemy engine from `DATABASE_URL`
- exposes `SessionLocal` for future database session usage

### `app/services/health_service.py`

- contains the health response logic

### `docker-compose.yml`

- defines the local PostgreSQL service
- defines the Adminer service for database inspection
- creates the named Docker volume `asm_postgres_data` for persistent database storage

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

Check the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Check the database connection:

```bash
curl http://127.0.0.1:8000/db-check
```

Stop the database services:

```bash
docker compose down
```
