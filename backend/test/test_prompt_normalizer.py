
import unittest

from app.security.normalizer import normalize_for_detection


class TestPromptNormalizer(unittest.TestCase):

    def test_lowercase_conversion(self):
        result = normalize_for_detection("IGNORE")
        self.assertEqual(result, "ignore")

    def test_whitespace_normalization(self):
        result = normalize_for_detection(
            "ignore    previous   instructions"
        )
        self.assertEqual(
            result,
            "ignore previous instructions"
        )

    def test_html_entity_decoding(self):
        result = normalize_for_detection(
            "&lt;script&gt;"
        )
        self.assertEqual(result, "<script>")

    def test_zero_width_removal(self):
        result = normalize_for_detection(
            "ig\u200bnore"
        )
        self.assertEqual(result, "ignore")

    def test_unicode_normalization(self):
        result = normalize_for_detection(
            "ＩＧＮＯＲＥ"
        )
        self.assertEqual(result, "ignore")

    def test_original_prompt_unchanged(self):
        original = "  IGNORE   PREVIOUS  "
        normalize_for_detection(original)

        self.assertEqual(
            original,
            "  IGNORE   PREVIOUS  "
        )


if __name__ == "__main__":
    unittest.main()
