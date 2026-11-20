
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db


router = APIRouter(
    tags=["Database"]
)


@router.get("/database-test")
def database_test(db: Session = Depends(get_db)):

    database_name = db.execute(
        text("SELECT current_database()")
    ).scalar_one()

    return {
        "status": "connected",
        "database": database_name,
        "message": "FastAPI successfully connected to PostgreSQL!"
    }
