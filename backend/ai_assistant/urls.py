"""
URL configuration for ai_assistant app.
"""
from django.urls import path
from .views import AIAssistantAskView

urlpatterns = [
    path(
        "ask/",
        AIAssistantAskView.as_view(),
        name="ai-assistant-ask",
    ),
]
