import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.routes import prompts
from app.models.user import User


class TestConnectionEndpoint(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()
        self.previous_db_override = app.dependency_overrides.get(get_db)

        def override_get_db():
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        if self.previous_db_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = self.previous_db_override

    def test_valid_api_key_returns_success_without_ai_or_audit_side_effects(self):
        with (
            patch.object(prompts, "generate_ai_response") as generate_response,
            patch.object(prompts, "inspect_prompt") as inspect_prompt,
        ):
            response = self.client.get(
                "/api/v1/prompt/connection-test",
                headers={"X-API-Key": "valid_connection_test_key"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "connected",
            "message": "Backend connection and API key authentication successful",
        })
        generate_response.assert_not_called()
        inspect_prompt.assert_not_called()
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_missing_api_key_is_rejected(self):
        response = self.client.get("/api/v1/prompt/connection-test")

        self.assertEqual(response.status_code, 401)
        self.db.query.assert_not_called()

    def test_invalid_api_key_is_rejected(self):
        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/api/v1/prompt/connection-test",
            headers={"X-API-Key": "invalid_connection_test_key"},
        )

        self.assertEqual(response.status_code, 401)
        self.db.query.assert_called_once_with(User)


if __name__ == "__main__":
    unittest.main()
