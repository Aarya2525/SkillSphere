"""
Provider factory for dynamically instantiating the configured AI provider.
"""
from django.conf import settings

from .base import BaseAIProvider, AIConfigurationError
from .gemini_provider import GeminiProvider
from .mock_provider import MockAIProvider


def get_ai_provider() -> BaseAIProvider:
    """
    Factory function returning the active AI provider based on Django settings.
    """
    provider_name = getattr(settings, "AI_PROVIDER", "gemini").strip().lower()

    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "mock":
        return MockAIProvider()
    else:
        raise AIConfigurationError(
            f"Unsupported or unknown AI provider: '{provider_name}'."
        )
