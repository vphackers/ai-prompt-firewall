
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from app.config import settings


# Build the PostgreSQL connection URL safely
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)


# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# Test the database connection
def test_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar_one()

            if value == 1:
                return True

    except Exception as error:
        print(f"Database connection failed: {type(error).__name__}")
        return False

    return False
