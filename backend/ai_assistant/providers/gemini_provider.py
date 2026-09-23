"""
Google Gemini AI provider implementation using Python standard library urllib.
Avoids adding external dependencies to the environment.
Implements header-based authentication and strict secret sanitization.
"""
import json
import urllib.error
import urllib.request
from django.conf import settings

from .base import (
    BaseAIProvider,
    AIConfigurationError,
    AIProviderError,
    AITimeoutError,
)


class GeminiProvider(BaseAIProvider):
    """
    Concrete AI provider communicating with Google Gemini REST API.
    Uses standard library urllib to avoid extra package dependencies.
    Passes API key securely via request headers to prevent URL query logging.
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        timeout: int = None,
    ):
        self.api_key = (
            api_key
            if api_key is not None
            else getattr(settings, "AI_API_KEY", "")
        )
        self.model = (
            model
            if model is not None
            else getattr(settings, "AI_MODEL", "gemini-1.5-flash")
        )
        self.timeout = (
            timeout
            if timeout is not None
            else getattr(settings, "AI_REQUEST_TIMEOUT", 30)
        )

    def _sanitize(self, message: str) -> str:
        """Strip API key or sensitive data from any message."""
        if self.api_key and self.api_key in message:
            return message.replace(self.api_key, "[REDACTED]")
        return message

    def generate_response(self, system_instruction: str, prompt: str) -> str:
        if not self.api_key or not self.api_key.strip():
            raise AIConfigurationError(
                "Gemini API key is not configured in environment."
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 1024,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status_code = response.getcode()
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            sanitized_reason = self._sanitize(str(exc.code))
            raise AIProviderError(
                f"Gemini API returned HTTP status {sanitized_reason}."
            ) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise AITimeoutError(
                    "Gemini API request timed out."
                ) from None
            sanitized_reason = self._sanitize(str(exc.reason))
            raise AIProviderError(
                f"Failed to communicate with Gemini API: {sanitized_reason}"
            ) from None
        except TimeoutError:
            raise AITimeoutError(
                "Gemini API request timed out."
            ) from None

        if status_code != 200:
            raise AIProviderError(
                f"Gemini API returned HTTP status {status_code}."
            )

        try:
            data = json.loads(response_body)
            candidates = data.get("candidates", [])
            if not candidates:
                raise AIProviderError("Gemini API returned no candidates.")

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason")
            if finish_reason == "SAFETY":
                raise AIProviderError("Gemini response was blocked by safety policy.")

            parts = candidate.get("content", {}).get("parts", [])
            if not parts:
                raise AIProviderError("Gemini API candidate contained no parts.")

            answer = parts[0].get("text", "")
            if not answer or not answer.strip():
                raise AIProviderError("Gemini API returned an empty response.")

            return answer.strip()
        except (ValueError, KeyError, IndexError) as exc:
            raise AIProviderError(
                "Failed to parse Gemini API response payload."
            ) from None
