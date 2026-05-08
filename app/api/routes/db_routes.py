from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import engine

router = APIRouter()


@router.get("/db-check")
def db_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database_connected": value == 1
    }
