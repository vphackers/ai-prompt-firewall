import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from fastapi import HTTPException

from app.config import Settings, settings
from app.routes import prompts
from app.schemas.prompt import PromptAnalyzeRequest
from app.services import ai_response_service
from app.services.ai_response_service import AIResponseError


class TestGroqModelConfiguration(unittest.TestCase):

    def test_default_model_is_gpt_oss_120b(self):
        with patch.dict(os.environ, {}, clear=True):
            configured = Settings(
                DB_HOST="localhost",
                DB_NAME="test",
                DB_USER="test",
                DB_PASSWORD="test",
                _env_file=None,
            )

        self.assertEqual(configured.GROQ_MODEL, "openai/gpt-oss-120b")


class TestAIResponseService(unittest.TestCase):

    def setUp(self):
        self.api_key_patch = patch.object(settings, "GROQ_API_KEY", "test-groq-key")
        self.api_key_patch.start()
        self.addCleanup(self.api_key_patch.stop)

        self.model_patch = patch.object(settings, "GROQ_MODEL", "test-model")
        self.model_patch.start()
        self.addCleanup(self.model_patch.stop)

    def _client_mock(self, response=None, side_effect=None):
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        if response is not None:
            client.post.return_value = response
        if side_effect is not None:
            client.post.side_effect = side_effect
        return client

    def test_extracts_response_and_sends_chat_completion_request(self):
        response = httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  A helpful answer.  "}}]},
            request=httpx.Request("POST", ai_response_service.GROQ_CHAT_COMPLETIONS_URL),
        )
        client = self._client_mock(response=response)

        with patch.object(ai_response_service.httpx, "Client", return_value=client) as client_factory:
            answer = ai_response_service.generate_ai_response("Explain firewalls.")

        self.assertEqual(answer, "A helpful answer.")
        timeout = client_factory.call_args.kwargs["timeout"]
        self.assertIsInstance(timeout, httpx.Timeout)
        self.assertEqual(timeout.connect, 5.0)
        self.assertEqual(timeout.read, 20.0)
        args, kwargs = client.post.call_args
        self.assertEqual(args[0], ai_response_service.GROQ_CHAT_COMPLETIONS_URL)
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-groq-key")
        self.assertEqual(kwargs["json"]["model"], "test-model")
        self.assertEqual(kwargs["json"]["messages"][1], {
            "role": "user",
            "content": "Explain firewalls.",
        })
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "system")
        self.assertEqual(kwargs["json"]["max_completion_tokens"], 512)
        self.assertNotIn("max_tokens", kwargs["json"])
        self.assertEqual(kwargs["json"]["temperature"], 0.3)

    def test_missing_api_key_fails_without_request(self):
        with patch.object(settings, "GROQ_API_KEY", None):
            with patch.object(ai_response_service.httpx, "Client") as client:
                with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                    with self.assertRaises(AIResponseError):
                        ai_response_service.generate_ai_response("Sensitive user prompt.")
        client.assert_not_called()
        self.assertIn("category=configuration_error", logs.output[0])
        self.assertNotIn("Sensitive user prompt", "\n".join(logs.output))

    def test_provider_timeout_is_sanitized(self):
        client = self._client_mock(side_effect=httpx.ReadTimeout("secret provider detail"))
        with patch.object(ai_response_service.httpx, "Client", return_value=client):
            with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError) as context:
                    ai_response_service.generate_ai_response("Sensitive user prompt.")

        self.assertEqual(str(context.exception), "AI response service timed out.")
        self.assertNotIn("secret provider detail", str(context.exception))
        self.assertIn("category=timeout", logs.output[0])
        self.assertNotIn("Sensitive user prompt", "\n".join(logs.output))

    def test_connection_error_is_logged_without_exception_details(self):
        request = httpx.Request("POST", ai_response_service.GROQ_CHAT_COMPLETIONS_URL)
        client = self._client_mock(
            side_effect=httpx.ConnectError("private connection detail", request=request)
        )
        with patch.object(ai_response_service.httpx, "Client", return_value=client):
            with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError):
                    ai_response_service.generate_ai_response("Sensitive user prompt.")

        self.assertIn("category=connection_error", logs.output[0])
        self.assertNotIn("private connection detail", "\n".join(logs.output))
        self.assertNotIn("Sensitive user prompt", "\n".join(logs.output))

    def test_provider_http_error_is_sanitized(self):
        response = httpx.Response(
            401,
            json={
                "error": {
                    "message": "private provider payload test-groq-key Sensitive user prompt",
                    "type": "authentication_error",
                    "code": "invalid_api_key",
                }
            },
            request=httpx.Request("POST", ai_response_service.GROQ_CHAT_COMPLETIONS_URL),
        )
        client = self._client_mock(response=response)
        with patch.object(ai_response_service.httpx, "Client", return_value=client):
            with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError) as context:
                    ai_response_service.generate_ai_response("Sensitive user prompt.")

        self.assertEqual(str(context.exception), "AI response service request failed.")
        log_output = "\n".join(logs.output)
        self.assertIn("category=provider_http_error status=401", log_output)
        self.assertIn("provider_error_type=authentication_error", log_output)
        self.assertIn("provider_error_code=invalid_api_key", log_output)
        self.assertNotIn("private provider payload", log_output)
        self.assertNotIn("test-groq-key", log_output)
        self.assertNotIn("Authorization", log_output)
        self.assertNotIn("Sensitive user prompt", log_output)

    def test_malformed_provider_json_fails_safely(self):
        response = httpx.Response(
            200,
            text="not-json",
            request=httpx.Request("POST", ai_response_service.GROQ_CHAT_COMPLETIONS_URL),
        )
        client = self._client_mock(response=response)
        with patch.object(ai_response_service.httpx, "Client", return_value=client):
            with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError):
                    ai_response_service.generate_ai_response("Sensitive user prompt.")

        self.assertIn("category=response_format_error", logs.output[0])
        self.assertNotIn("not-json", "\n".join(logs.output))
        self.assertNotIn("Sensitive user prompt", "\n".join(logs.output))

    def test_missing_response_content_fails_safely(self):
        response = httpx.Response(
            200,
            json={"choices": [{"message": {"content": ""}}]},
            request=httpx.Request("POST", ai_response_service.GROQ_CHAT_COMPLETIONS_URL),
        )
        client = self._client_mock(response=response)
        with patch.object(ai_response_service.httpx, "Client", return_value=client):
            with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError):
                    ai_response_service.generate_ai_response("Sensitive user prompt.")

        self.assertIn("category=response_format_error", logs.output[0])

    def test_provider_error_identifiers_with_unsafe_characters_are_omitted(self):
        response = httpx.Response(
            500,
            json={
                "error": {
                    "type": "provider error with detail",
                    "code": "sensitive-code-test-groq-key",
                    "message": "private provider response",
                }
            },
            request=httpx.Request("POST", ai_response_service.GROQ_CHAT_COMPLETIONS_URL),
        )
        client = self._client_mock(response=response)
        with patch.object(ai_response_service.httpx, "Client", return_value=client):
            with self.assertLogs("app.services.ai_response_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError):
                    ai_response_service.generate_ai_response("Sensitive user prompt.")

        log_output = "\n".join(logs.output)
        self.assertIn("provider_error_type=unavailable", log_output)
        self.assertIn("provider_error_code=unavailable", log_output)
        self.assertNotIn("sensitive-code-test-groq-key", log_output)
        self.assertNotIn("private provider response", log_output)
        self.assertNotIn("Sensitive user prompt", log_output)


class TestPromptAnalysisAIIntegration(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.user = SimpleNamespace(id=123)
        self.safe_analysis = {
            "is_suspicious": False,
            "total_findings": 0,
            "findings": [],
            "risk_score": 0,
            "risk_status": "SAFE",
            "detected_categories": [],
        }

        self.rate_limit_patch = patch.object(prompts, "check_rate_limit")
        self.rate_limit_patch.start()
        self.addCleanup(self.rate_limit_patch.stop)

        self.inspect_patch = patch.object(prompts, "inspect_prompt", return_value=self.safe_analysis)
        self.inspect_mock = self.inspect_patch.start()
        self.addCleanup(self.inspect_patch.stop)

    @patch.object(prompts, "generate_ai_response", return_value="Real AI answer.")
    def test_safe_prompt_calls_ai_and_logs_response(self, generate_response):
        call_order = []
        self.inspect_mock.side_effect = lambda prompt: (
            call_order.append("inspect") or self.safe_analysis
        )
        generate_response.side_effect = lambda prompt: (
            call_order.append("provider") or "Real AI answer."
        )

        result = prompts.analyze_prompt(
            PromptAnalyzeRequest(prompt="A safe prompt."),
            self.db,
            self.user,
        )

        generate_response.assert_called_once_with("A safe prompt.")
        self.assertEqual(call_order, ["inspect", "provider"])
        audit_log = self.db.add.call_args.args[0]
        self.assertEqual(audit_log.risk_status, "SAFE")
        self.assertEqual(audit_log.ai_response, "Real AI answer.")
        self.db.commit.assert_called_once()
        self.assertEqual(result["ai_response"], "Real AI answer.")

    @patch.object(prompts, "generate_ai_response")
    def test_blocked_prompt_never_calls_ai_and_is_logged_before_403(self, generate_response):
        blocked_analysis = {
            **self.safe_analysis,
            "is_suspicious": True,
            "total_findings": 1,
            "findings": [{"category": "injection", "description": "blocked"}],
            "risk_score": 100,
            "risk_status": "BLOCKED",
            "detected_categories": ["injection"],
        }
        with patch.object(prompts, "inspect_prompt", return_value=blocked_analysis):
            with self.assertRaises(HTTPException) as context:
                prompts.analyze_prompt(
                    PromptAnalyzeRequest(prompt="Unsafe prompt."),
                    self.db,
                    self.user,
                )

        generate_response.assert_not_called()
        self.assertEqual(context.exception.status_code, 403)
        audit_log = self.db.add.call_args.args[0]
        self.assertEqual(audit_log.risk_status, "BLOCKED")
        self.assertIsNotNone(audit_log.block_reason)
        self.db.commit.assert_called_once()

    @patch.object(prompts, "generate_ai_response", side_effect=AIResponseError("provider detail"))
    def test_safe_prompt_ai_failure_is_logged_and_returns_503(self, generate_response):
        with self.assertRaises(HTTPException) as context:
            prompts.analyze_prompt(
                PromptAnalyzeRequest(prompt="A safe prompt."),
                self.db,
                self.user,
            )

        generate_response.assert_called_once()
        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(
            context.exception.detail,
            "AI response service is temporarily unavailable.",
        )
        audit_log = self.db.add.call_args.args[0]
        self.assertEqual(audit_log.risk_status, "SAFE")
        self.assertIsNone(audit_log.ai_response)
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
