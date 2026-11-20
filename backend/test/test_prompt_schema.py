
import unittest
from typing import cast

from pydantic import ValidationError

from app.schemas.prompt import PromptAnalyzeRequest


class TestPromptValidation(unittest.TestCase):

    def test_valid_prompt(self):
        data = PromptAnalyzeRequest(
            prompt="Explain cybersecurity."
        )

        self.assertEqual(
            data.prompt,
            "Explain cybersecurity."
        )

    def test_empty_prompt(self):
        with self.assertRaises(ValidationError):
            PromptAnalyzeRequest(
                prompt=""
            )

    def test_whitespace_prompt(self):
        with self.assertRaises(ValidationError):
            PromptAnalyzeRequest(
                prompt="   "
            )

    def test_wrong_data_type(self):
        with self.assertRaises(ValidationError):
            PromptAnalyzeRequest(
                prompt=cast(str, 12345)
            )

    def test_prompt_too_long(self):
        with self.assertRaises(ValidationError):
            PromptAnalyzeRequest(
                prompt="A" * 10001
            )

    def test_prompt_maximum_valid_length(self):
        data = PromptAnalyzeRequest(
            prompt="A" * 10000
        )

        self.assertEqual(len(data.prompt), 10000)

    def test_missing_prompt(self):
        with self.assertRaises(ValidationError):
            PromptAnalyzeRequest.model_validate({})


if __name__ == "__main__":
    unittest.main()
