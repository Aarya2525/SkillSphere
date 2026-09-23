"""
Mock AI provider for automated testing and offline development.
"""
from .base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Deterministic mock provider for automated test suites and local development.
    Avoids external network calls and third-party rate limits.
    """

    def __init__(self, response_text: str = None):
        self.response_text = (
            response_text
            if response_text is not None
            else "This is a helpful explanation from the SkillSphere AI tutor."
        )

    def generate_response(self, system_instruction: str, prompt: str) -> str:
        return self.response_text
