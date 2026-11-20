
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.security.api_key_auth import get_current_user
from app.services.user_service import hash_api_key


class TestAPIKeyAuthentication(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

    def test_missing_api_key(self):

        with self.assertRaises(HTTPException) as context:
            get_current_user(None, self.db)

        self.assertEqual(
            context.exception.status_code,
            401
        )

    def test_invalid_api_key(self):

        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            get_current_user("invalid_key", self.db)

        self.assertEqual(
            context.exception.status_code,
            401
        )

    def test_valid_api_key(self):

        expected_user = MagicMock()
        expected_user.id = 123

        self.db.query.return_value.filter.return_value.first.return_value = expected_user

        result = get_current_user("valid_test_key", self.db)

        self.assertEqual(result.id, 123)

    def test_api_key_hashing(self):

        key = "test_api_key"

        hashed_key = hash_api_key(key)

        self.assertEqual(len(hashed_key), 64)
        self.assertNotEqual(hashed_key, key)


if __name__ == "__main__":
    unittest.main()
