
import unittest

from app.security.regex_detector import detect_regex_threats


class TestRegexDetection(unittest.TestCase):

    def test_script_detection(self):
        result = detect_regex_threats(
            "<script>alert(1)</script>"
        )
        self.assertTrue(
            any(item["category"] == "XSS" for item in result)
        )

    def test_event_attribute_detection(self):
        result = detect_regex_threats(
            "<img src=x onerror=alert(1)>"
        )
        self.assertTrue(
            any(item["category"] == "XSS" for item in result)
        )

    def test_javascript_scheme_detection(self):
        result = detect_regex_threats(
            "javascript:alert(1)"
        )
        self.assertTrue(
            any(item["category"] == "XSS" for item in result)
        )

    def test_sql_union_detection(self):
        result = detect_regex_threats(
            "UNION SELECT username FROM users"
        )
        self.assertTrue(
            any(item["category"] == "SQL_INJECTION" for item in result)
        )

    def test_drop_table_detection(self):
        result = detect_regex_threats(
            "DROP TABLE users"
        )
        self.assertTrue(
            any(item["category"] == "SQL_INJECTION" for item in result)
        )

    def test_safe_prompt(self):
        result = detect_regex_threats(
            "Explain how Python functions work."
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
