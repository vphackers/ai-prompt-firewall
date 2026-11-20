
import unittest

from db_test_config import (
    TestSessionLocal,
    verify_test_database,
    create_test_tables,
)

from app.models.user import User
from app.models.audit_log import PromptAuditLog
from app.services.audit_log_service import get_all_audit_logs


class TestAuditLogIsolationIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        verify_test_database()
        create_test_tables()

    def setUp(self):
        self.db = TestSessionLocal()

        # Create two independent users
        self.user_a = User(
            name="BOLA Test User A",
            email="bola_user_a@test.local",
            api_key="test_hash_user_a"
        )

        self.user_b = User(
            name="BOLA Test User B",
            email="bola_user_b@test.local",
            api_key="test_hash_user_b"
        )

        self.db.add_all([self.user_a, self.user_b])
        self.db.flush()

        # Create audit logs for User A
        self.log_a = PromptAuditLog(
            user_id=self.user_a.id,
            raw_prompt="User A safe prompt",
            sanitized_prompt="User A safe prompt",
            risk_status="SAFE"
        )

        # Create audit logs for User B
        self.log_b = PromptAuditLog(
            user_id=self.user_b.id,
            raw_prompt="User B blocked prompt",
            sanitized_prompt="User B blocked prompt",
            risk_status="BLOCKED"
        )

        self.db.add_all([self.log_a, self.log_b])
        self.db.commit()

    def tearDown(self):
        self.db.rollback()

        # Delete audit records before deleting users
        self.db.query(PromptAuditLog).filter(
            PromptAuditLog.user_id.in_(
                [self.user_a.id, self.user_b.id]
            )
        ).delete(synchronize_session=False)

        self.db.query(User).filter(
            User.id.in_([self.user_a.id, self.user_b.id])
        ).delete(synchronize_session=False)

        self.db.commit()
        self.db.close()

    def test_user_a_cannot_access_user_b_logs(self):
        logs = get_all_audit_logs(
            db=self.db,
            user_id=self.user_a.id
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].user_id, self.user_a.id)

    def test_user_b_cannot_access_user_a_logs(self):
        logs = get_all_audit_logs(
            db=self.db,
            user_id=self.user_b.id
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].user_id, self.user_b.id)

    def test_user_a_receives_only_own_records(self):
        logs = get_all_audit_logs(
            db=self.db,
            user_id=self.user_a.id
        )

        self.assertTrue(
            all(log.user_id == self.user_a.id for log in logs)
        )

    def test_user_b_receives_only_own_records(self):
        logs = get_all_audit_logs(
            db=self.db,
            user_id=self.user_b.id
        )

        self.assertTrue(
            all(log.user_id == self.user_b.id for log in logs)
        )

    def test_risk_status_filter_preserves_user_isolation(self):
        logs = get_all_audit_logs(
            db=self.db,
            user_id=self.user_a.id,
            risk_status="SAFE"
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].user_id, self.user_a.id)
        self.assertEqual(logs[0].risk_status, "SAFE")

    def test_pagination_preserves_user_isolation(self):
        logs = get_all_audit_logs(
            db=self.db,
            user_id=self.user_a.id,
            skip=0,
            limit=1
        )

        self.assertEqual(len(logs), 1)

        for log in logs:
            self.assertEqual(log.user_id, self.user_a.id)


if __name__ == "__main__":
    unittest.main()
