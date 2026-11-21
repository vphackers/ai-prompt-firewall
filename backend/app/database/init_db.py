from app.database.connection import engine
from app.models import Base


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
