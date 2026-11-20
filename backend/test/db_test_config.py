
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.base import Base

# Import models to register their tables with Base.metadata
from app.models.user import User
from app.models.audit_log import PromptAuditLog


TEST_DATABASE_NAME = "ai_prompt_firewall_test"

# Build a separate PostgreSQL connection
TEST_DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=TEST_DATABASE_NAME,
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False
)


def verify_test_database():
    """
    Ensure tests connect only to the dedicated test database.
    """

    with test_engine.connect() as connection:
        current_database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if current_database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "Safety check failed: incorrect test database."
            )

    return True


def create_test_tables():
    verify_test_database()
    Base.metadata.create_all(bind=test_engine)


def drop_test_tables():
    verify_test_database()
    Base.metadata.drop_all(bind=test_engine)
