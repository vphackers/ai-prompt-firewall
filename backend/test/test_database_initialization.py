import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.database import init_db
from app.main import app
from app.models import Base, User


class TestDatabaseInitialization(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite://")

    def tearDown(self):
        self.engine.dispose()

    def test_creates_missing_tables_idempotently_and_preserves_existing_data(self):
        with self.engine.begin() as connection:
            User.__table__.create(bind=connection)
            connection.execute(
                User.__table__.insert().values(
                    id=1,
                    name="Existing User",
                    email="existing@example.test",
                    api_key="stored-test-hash",
                )
            )

        with patch.object(init_db, "engine", self.engine):
            init_db.initialize_database()
            init_db.initialize_database()

        self.assertEqual(
            set(Base.metadata.tables),
            {"users", "prompt_audit_logs"},
        )
        self.assertEqual(
            set(inspect(self.engine).get_table_names()),
            {"users", "prompt_audit_logs"},
        )
        with Session(self.engine) as session:
            user = session.get(User, 1)

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "existing@example.test")

    def test_application_startup_initializes_database(self):
        with patch("app.main.initialize_database") as initialize:
            with TestClient(app):
                initialize.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
