
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_db
from app.models.user import User
from app.models.audit_log import PromptAuditLog
from app.services.user_service import hash_api_key

from db_test_config import (
    TestSessionLocal,
    verify_test_database,
    create_test_tables,
)


class TestBOLAAPIIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        verify_test_database()
        create_test_tables()

        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        self.db = TestSessionLocal()

        # Create two independent API users
        self.key_a = "bola_test_api_key_user_a"
        self.key_b = "bola_test_api_key_user_b"

        self.user_a = User(
            name="API Test User A",
            email="api_bola_a@test.local",
            api_key=hash_api_key(self.key_a)
        )

        self.user_b = User(
            name="API Test User B",
            email="api_bola_b@test.local",
            api_key=hash_api_key(self.key_b)
        )

        self.db.add_all([self.user_a, self.user_b])
        self.db.flush()

        # Create one audit record for each user
        self.db.add_all([
            PromptAuditLog(
                user_id=self.user_a.id,
                raw_prompt="User A private prompt",
                sanitized_prompt="User A private prompt",
                risk_status="SAFE"
            ),
            PromptAuditLog(
                user_id=self.user_b.id,
                raw_prompt="User B private prompt",
                sanitized_prompt="User B private prompt",
                risk_status="BLOCKED"
            )
        ])

        self.db.commit()

    def tearDown(self):
        try:
            self.db.query(PromptAuditLog).filter(
                PromptAuditLog.user_id.in_(
                    [self.user_a.id, self.user_b.id]
                )
            ).delete(synchronize_session=False)

            self.db.query(User).filter(
                User.id.in_(
                    [self.user_a.id, self.user_b.id]
                )
            ).delete(synchronize_session=False)

            self.db.commit()

        finally:
            self.db.close()

    def test_user_a_can_access_own_logs(self):
        response = self.client.get(
            "/api/v1/prompt/audit-logs",
            headers={"X-API-Key": self.key_a}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["raw_prompt"],
            "User A private prompt"
        )

    def test_user_b_can_access_own_logs(self):
        response = self.client.get(
            "/api/v1/prompt/audit-logs",
            headers={"X-API-Key": self.key_b}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["raw_prompt"],
            "User B private prompt"
        )

    def test_user_a_cannot_access_user_b_logs(self):
        response = self.client.get(
            f"/api/v1/prompt/audit-logs?user_id={self.user_b.id}",
            headers={"X-API-Key": self.key_a}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        for log in response.json():
            self.assertEqual(
                log["raw_prompt"],
                "User A private prompt"
            )

    def test_missing_api_key_is_rejected(self):
        response = self.client.get(
            "/api/v1/prompt/audit-logs"
        )

        self.assertEqual(response.status_code, 401)

    def test_invalid_api_key_is_rejected(self):
        response = self.client.get(
            "/api/v1/prompt/audit-logs",
            headers={"X-API-Key": "invalid_bola_test_key"}
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
