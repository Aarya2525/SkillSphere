"""
Rate throttling for AI Learning Assistant.
Protects AI endpoints against abuse while allowing normal learning flow.
"""
from django.conf import settings
from rest_framework.throttling import UserRateThrottle


class AIAssistantRateThrottle(UserRateThrottle):
    """
    Dedicated throttle for the AI Assistant endpoint.
    Scoped specifically to 'ai_assistant' so other APIs are unaffected.
    Dynamically resolves rate settings to support runtime and test overrides.
    """
    scope = "ai_assistant"

    def get_rate(self):
        """
        Dynamically determine the rate string from settings or environment.
        Supports runtime override_settings and dynamic reconfiguration.
        """
        rf_settings = getattr(settings, "REST_FRAMEWORK", {})
        rates = rf_settings.get("DEFAULT_THROTTLE_RATES", {})
        if self.scope in rates:
            return rates[self.scope]
        return getattr(settings, "AI_RATE_LIMIT", "30/minute")

    def __init__(self):
        super().__init__()
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }
