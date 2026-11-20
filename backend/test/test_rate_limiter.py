
import unittest

from fastapi import HTTPException

from app.security.rate_limiter import (
    check_rate_limit,
    request_history
)


class TestRateLimiter(unittest.TestCase):

    def setUp(self):
        request_history.clear()

    def test_allow_requests_within_limit(self):

        for _ in range(15):
            check_rate_limit(1)

    def test_block_sixteenth_request(self):

        for _ in range(15):
            check_rate_limit(1)

        with self.assertRaises(HTTPException) as context:
            check_rate_limit(1)

        self.assertEqual(
            context.exception.status_code,
            429
        )

    def test_separate_user_limits(self):

        for _ in range(15):
            check_rate_limit(1)

        # Another user should still be allowed
        check_rate_limit(2)

    def test_different_users_have_separate_counters(self):

        check_rate_limit(1)
        check_rate_limit(2)

        self.assertEqual(len(request_history[1]), 1)
        self.assertEqual(len(request_history[2]), 1)


if __name__ == "__main__":
    unittest.main()
