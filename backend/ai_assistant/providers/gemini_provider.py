"""
Google Gemini AI provider implementation using Python standard library urllib.
Avoids adding external dependencies to the environment.
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

    def generate_response(self, system_instruction: str, prompt: str) -> str:
        if not self.api_key or not self.api_key.strip():
            raise AIConfigurationError(
                "Gemini API key is not configured in environment."
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
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
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status_code = response.getcode()
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise AIProviderError(
                f"Gemini API returned HTTP status {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise AITimeoutError(
                    "Gemini API request timed out."
                ) from exc
            raise AIProviderError(
                f"Failed to communicate with Gemini API: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise AITimeoutError(
                "Gemini API request timed out."
            ) from exc

        if status_code != 200:
            raise AIProviderError(
                f"Gemini API returned HTTP status {status_code}."
            )

        try:
            data = json.loads(response_body)
            candidates = data.get("candidates", [])
            if not candidates:
                raise AIProviderError("Gemini API returned no candidates.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise AIProviderError("Gemini API candidate contained no parts.")

            answer = parts[0].get("text", "")
            return answer.strip()
        except (ValueError, KeyError, IndexError) as exc:
            raise AIProviderError(
                "Failed to parse Gemini API response payload."
            ) from exc
