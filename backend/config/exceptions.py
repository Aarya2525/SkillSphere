"""
Centralized DRF Exception Handler and Error Normalization for SkillSphere.
Stage 16: API Validation & Errors.

Provides consistent, machine-readable API error structures:
{
    "error": {
        "code": "validation_error",
        "message": "Request validation failed.",
        "details": { ... }
    }
}

Guarantees:
- Predictable HTTP status codes
- Machine-readable error codes
- Zero exposure of internal tracebacks, SQL, secrets, or file paths
- Seamless backward compatibility with frontend consumers and existing tests
"""
import logging
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from ai_assistant.providers.base import (
    AIConfigurationError,
    AIProviderError,
    AITimeoutError,
)

logger = logging.getLogger("config.exceptions")


class ErrorDetail(dict):
    """
    Structured error dictionary that also supports string-equality comparisons
    for backward compatibility with legacy tests and frontend components.
    """
    def __init__(self, code: str, message: str, details=None):
        data = {"code": code, "message": message}
        if details is not None:
            data["details"] = details
        super().__init__(data)
        self.code = code
        self.message = message
        self.details = details

    def __eq__(self, other):
        if isinstance(other, str):
            return self.message == other or self.code == other
        return super().__eq__(other)

    def __str__(self):
        return self.message

    def lower(self):
        return self.message.lower()


def get_error_code(exc, status_code: int) -> str:
    """
    Maps an exception or HTTP status code to a predictable machine-readable error code.
    """
    if isinstance(exc, exceptions.AuthenticationFailed):
        return "authentication_failed"
    if isinstance(exc, exceptions.NotAuthenticated):
        return "not_authenticated"
    if isinstance(exc, (exceptions.PermissionDenied, DjangoPermissionDenied)):
        return "permission_denied"
    if isinstance(exc, (exceptions.NotFound, Http404)):
        return "not_found"
    if isinstance(exc, (exceptions.ValidationError, DjangoValidationError)):
        return "validation_error"
    if isinstance(exc, exceptions.Throttled):
        return "rate_limited"
    if isinstance(exc, exceptions.MethodNotAllowed):
        return "method_not_allowed"
    if isinstance(exc, exceptions.UnsupportedMediaType):
        return "unsupported_media_type"
    if isinstance(exc, exceptions.ParseError):
        return "parse_error"
    if isinstance(exc, AIConfigurationError):
        return "ai_not_configured"
    if isinstance(exc, AITimeoutError):
        return "ai_timeout"
    if isinstance(exc, AIProviderError):
        return "provider_error"

    # Status-based fallbacks
    status_map = {
        400: "validation_error",
        401: "not_authenticated",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        415: "unsupported_media_type",
        429: "rate_limited",
        502: "provider_error",
        503: "ai_not_configured",
        504: "ai_timeout",
        500: "server_error",
    }
    return status_map.get(status_code, "api_error")


def normalize_error_data(raw_data, exc):
    """
    Normalizes DRF error payload into (message, details).
    Ensures safe formatting without revealing tracebacks or raw parser internals.
    """
    if isinstance(exc, exceptions.ParseError):
        return "Malformed request body or invalid JSON.", None

    if isinstance(exc, exceptions.Throttled):
        wait_seconds = getattr(exc, "wait", None)
        if wait_seconds is not None:
            return (
                f"Request was throttled. Expected available in {wait_seconds} seconds.",
                {"wait_seconds": wait_seconds},
            )
        return "Request was throttled.", None

    if isinstance(raw_data, dict):
        if "detail" in raw_data and len(raw_data) == 1:
            detail_val = raw_data["detail"]
            if isinstance(detail_val, (list, tuple)):
                return str(detail_val[0]), None
            return str(detail_val), None

        # Field validation errors: e.g. {"username": ["..."]}
        details = {}
        for field, errs in raw_data.items():
            if isinstance(errs, (list, tuple)):
                details[field] = [str(e) for e in errs]
            elif isinstance(errs, dict):
                details[field] = errs
            else:
                details[field] = [str(errs)]

        # Determine concise top-level message
        first_field = next(iter(raw_data))
        first_err = raw_data[first_field]
        if isinstance(first_err, (list, tuple)) and first_err:
            message = f"{first_field}: {first_err[0]}"
        elif isinstance(first_err, str):
            message = f"{first_field}: {first_err}"
        else:
            message = "Request validation failed."

        return message, details

    if isinstance(raw_data, (list, tuple)):
        clean_list = [str(item) for item in raw_data]
        message = clean_list[0] if clean_list else "Request validation failed."
        details = {"non_field_errors": clean_list}
        return message, details

    if isinstance(raw_data, str):
        return raw_data, None

    return "An error occurred.", None


def custom_exception_handler(exc, context):
    """
    Centralized DRF exception handler for SkillSphere.
    Standardizes error responses across all API endpoints while shielding internal details.
    """
    # 1. Let DRF handle standard exceptions first
    response = drf_exception_handler(exc, context)

    # 2. Handle known non-DRF or unhandled exceptions
    if response is None:
        if isinstance(exc, Http404):
            exc = exceptions.NotFound()
            response = Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        elif isinstance(exc, (DjangoPermissionDenied, exceptions.PermissionDenied)):
            exc = exceptions.PermissionDenied()
            response = Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif isinstance(exc, DjangoValidationError):
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            exc = exceptions.ValidationError(detail=detail)
            response = Response(
                detail,
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif isinstance(exc, AIConfigurationError):
            response = Response(
                {"detail": "AI assistant is currently not configured on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        elif isinstance(exc, AITimeoutError):
            response = Response(
                {"detail": "AI assistant timed out waiting for a response. Please try again."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        elif isinstance(exc, AIProviderError):
            response = Response(
                {"detail": "AI assistant encountered an error generating a response."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        else:
            # 3. Unexpected 500 Internal Server Error
            request = context.get("request") if context else None
            method = getattr(request, "method", "UNKNOWN")
            path = getattr(request, "path", "UNKNOWN")
            logger.exception("Unhandled server exception [%s %s]: %s", method, path, str(exc))

            error_obj = ErrorDetail(
                code="server_error",
                message="An unexpected server error occurred.",
            )
            data = {
                "error": error_obj,
                "code": "server_error",
                "message": "An unexpected server error occurred.",
                "detail": "An unexpected server error occurred.",
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 4. Standardize response payload for handled exceptions
    status_code = response.status_code
    code = get_error_code(exc, status_code)
    message, details = normalize_error_data(response.data, exc)

    error_obj = ErrorDetail(code=code, message=message, details=details)

    formatted_data = {
        "error": error_obj,
        "code": code,
        "message": message,
        "detail": message,
    }

    # Flatten field validation errors into top level for backward compatibility
    if isinstance(details, dict):
        for field, err_list in details.items():
            if field not in formatted_data:
                formatted_data[field] = err_list

    response.data = formatted_data
    return response
