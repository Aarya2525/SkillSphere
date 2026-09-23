"""
Base definitions and exceptions for AI providers.
"""
from abc import ABC, abstractmethod


class AIError(Exception):
    """Base exception for all AI assistant operations."""
    pass


class AIConfigurationError(AIError):
    """Raised when an AI provider is missing required credentials or settings."""
    pass


class AITimeoutError(AIError):
    """Raised when a request to an AI provider times out."""
    pass


class AIProviderError(AIError):
    """Raised when an AI provider returns an error or invalid response."""
    pass


class BaseAIProvider(ABC):
    """
    Abstract interface for AI model completion providers.
    All concrete providers (e.g., Gemini, OpenAI, Mock) must implement this.
    """

    @abstractmethod
    def generate_response(self, system_instruction: str, prompt: str) -> str:
        """
        Generate a text response given a system instruction and user prompt.

        :param system_instruction: Educational guidelines and tutor persona.
        :param prompt: Contextual prompt containing lesson material and student query.
        :return: Generated text answer.
        :raises AIConfigurationError: If provider configuration is invalid or missing.
        :raises AITimeoutError: If the external provider times out.
        :raises AIProviderError: If the provider returns an error or invalid payload.
        """
        pass
