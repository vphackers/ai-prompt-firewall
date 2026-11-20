
import unittest

from app.security.risk_engine import calculate_risk


class TestRiskEngine(unittest.TestCase):

    def test_safe_prompt(self):

        result = calculate_risk([])

        self.assertEqual(result["risk_score"], 0)
        self.assertEqual(result["risk_status"], "SAFE")

    def test_prompt_injection_risk(self):

        findings = [
            {"category": "PROMPT_INJECTION"}
        ]

        result = calculate_risk(findings)

        self.assertEqual(result["risk_score"], 40)
        self.assertEqual(result["risk_status"], "FLAGGED")

    def test_xss_blocking(self):

        findings = [
            {"category": "XSS"}
        ]

        result = calculate_risk(findings)

        self.assertEqual(result["risk_score"], 50)
        self.assertEqual(result["risk_status"], "BLOCKED")

    def test_multiple_threat_categories(self):

        findings = [
            {"category": "PROMPT_INJECTION"},
            {"category": "XSS"}
        ]

        result = calculate_risk(findings)

        self.assertEqual(result["risk_score"], 90)
        self.assertEqual(result["risk_status"], "BLOCKED")

    def test_duplicate_category(self):

        findings = [
            {"category": "XSS"},
            {"category": "XSS"},
            {"category": "XSS"}
        ]

        result = calculate_risk(findings)

        self.assertEqual(result["risk_score"], 50)
        self.assertEqual(result["risk_status"], "BLOCKED")

    def test_unknown_category(self):

        findings = [
            {"category": "UNKNOWN_THREAT"}
        ]

        result = calculate_risk(findings)

        self.assertEqual(result["risk_score"], 10)
        self.assertEqual(result["risk_status"], "SAFE")


if __name__ == "__main__":
    unittest.main()
