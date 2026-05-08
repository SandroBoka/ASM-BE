# ASM-BE

Backend service for the FER Information Systems course project, built with FastAPI.

## Requirements

- Python 3.10 or newer
- `pip`

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

## Running the Application

Start the development server with:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`

## API Documentation

FastAPI generates interactive documentation automatically:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Available Endpoint

### `GET /health`

Health check endpoint used to verify that the backend is running.

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

## Project Structure

```text
ASM-BE/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health_routes.py
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
- defines project metadata such as title and version
- registers API routers

### `app/api/routes/health_routes.py`

- defines the `/health` route
- delegates response generation to the service layer

### `app/services/health_service.py`

- contains the current health check business logic
- returns the response payload for the health endpoint

### `app/schemas/`

- reserved for request and response schemas
- currently empty except for package initialization

### `app/repositories/`

- reserved for data access logic
- currently empty except for package initialization

## Development Notes

- The project currently uses a small layered structure: routes call services, and services hold backend logic.
- There is no database, authentication, configuration file, or test suite yet.
- Additional routers, schemas, repositories, and services can be added under the existing package layout.

## Common Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn app.main:app --reload
```

Update dependency versions later if needed:

```bash
pip freeze > requirements.txt
```
