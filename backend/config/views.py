from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


def check_database_health() -> bool:
    """Check whether database connection can successfully execute SELECT 1."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


class HealthCheckView(APIView):
    """
    Application Health Check View (Stage 22.4).
    Validates backend operational status and database connectivity.

    Responses:
    - 200 OK: {"status": "healthy", "database": "connected"}
    - 503 SERVICE_UNAVAILABLE: {"status": "unhealthy", "database": "disconnected"}

    Security & Privacy:
    - Never exposes hostnames, ports, credentials, stack traces, or exception details.
    - Excluded from authentication and throttling for orchestrator/Docker probes.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request, *args, **kwargs):
        db_ok = check_database_health()
        payload = {
            "status": "healthy" if db_ok else "unhealthy",
            "database": "connected" if db_ok else "disconnected",
        }
        status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return JsonResponse(payload, status=status_code)
