
import unittest
from unittest.mock import MagicMock

from app.models.audit_log import PromptAuditLog
from app.services.audit_log_service import get_all_audit_logs


class TestAuditLogService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

        self.query = self.db.query.return_value
        self.query.filter.return_value = self.query
        self.query.order_by.return_value = self.query
        self.query.offset.return_value = self.query
        self.query.limit.return_value = self.query

    def test_user_a_gets_only_user_a_logs(self):
        get_all_audit_logs(
            db=self.db,
            user_id=1
        )

        # Verify that the database query filters by User A
        self.query.filter.assert_called_once()
        self.assertTrue(
            self.query.filter.call_args.args[0].compare(
                PromptAuditLog.user_id == 1
            )
        )

    def test_user_b_gets_only_user_b_logs(self):
        get_all_audit_logs(
            db=self.db,
            user_id=2
        )

        # Verify that the database query filters by User B
        self.query.filter.assert_called_once()
        self.assertTrue(
            self.query.filter.call_args.args[0].compare(
                PromptAuditLog.user_id == 2
            )
        )

    def test_user_filter_is_always_applied(self):
        get_all_audit_logs(
            db=self.db,
            user_id=1
        )

        # A user filter must always be applied
        self.assertEqual(
            self.query.filter.call_count,
            1
        )

    def test_risk_status_filter(self):
        get_all_audit_logs(
            db=self.db,
            user_id=1,
            risk_status="BLOCKED"
        )

        # First filter: user ID
        # Second filter: risk status
        self.assertEqual(
            self.query.filter.call_count,
            2
        )

    def test_pagination_is_applied(self):
        get_all_audit_logs(
            db=self.db,
            user_id=1,
            skip=10,
            limit=20
        )

        self.query.offset.assert_called_once_with(10)
        self.query.limit.assert_called_once_with(20)

    def test_newest_logs_first(self):
        get_all_audit_logs(
            db=self.db,
            user_id=1
        )

        self.query.order_by.assert_called_once()
        self.assertTrue(
            self.query.order_by.call_args.args[0].compare(
                PromptAuditLog.created_at.desc()
            )
        )


if __name__ == "__main__":
    unittest.main()
