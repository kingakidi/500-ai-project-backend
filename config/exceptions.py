from django.db import DatabaseError, IntegrityError, OperationalError, ProgrammingError
from django.http import JsonResponse
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import exception_handler
from utils.response import APIResponse


def _stringify_detail(detail):
    try:
        return str(detail)
    except Exception:
        return "Invalid value"


def _normalize_errors(detail):
    """
    Convert DRF/Django exception detail to a consistent, human-friendly `error` object.
    Shape:
    - field errors: { "field": ["msg1", "msg2"], ... }
    - non-field: { "non_field_errors": ["msg"] }
    """
    if detail is None:
        return {}

    if isinstance(detail, list):
        return {"non_field_errors": [_stringify_detail(x) for x in detail]}

    if isinstance(detail, dict):
        normalized = {}
        for key, value in detail.items():
            if isinstance(value, list):
                normalized[key] = [_stringify_detail(x) for x in value]
            elif isinstance(value, dict):
                normalized[key] = value
            else:
                normalized[key] = [_stringify_detail(value)]
        return normalized

    return {"non_field_errors": [_stringify_detail(detail)]}


def custom_exception_handler(exc, context):
    if isinstance(exc, (NotFound, Http404)):
        return APIResponse.not_found("Route not found")

    if isinstance(exc, PermissionDenied):
        return APIResponse.forbidden("Permission denied")

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return APIResponse.unauthorized("Authentication required")

    if isinstance(exc, MethodNotAllowed):
        return APIResponse.error(
            message="Method not allowed",
            error={"method": [_stringify_detail(getattr(exc, "detail", ""))]},
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    if isinstance(exc, ParseError):
        return APIResponse.bad_request(
            "Invalid request payload",
            error={"payload": ["Malformed JSON or invalid request body."]},
        )

    if isinstance(exc, ValidationError):
        return APIResponse.validation_error(
            "Invalid request payload",
            _normalize_errors(getattr(exc, "detail", None)),
        )

    if isinstance(exc, IntegrityError):
        return APIResponse.duplicate("Duplicate record", error={"detail": [str(exc)]})

    if isinstance(exc, Throttled):
        retry_after = getattr(exc, "wait", None)
        err = {"detail": ["Too many requests. Please try again later."]}
        if retry_after is not None:
            err["retry_after_seconds"] = [str(int(retry_after))]
        return APIResponse.error(
            message="Too many requests",
            error=err,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if isinstance(exc, (DatabaseError, OperationalError, ProgrammingError)):
        return APIResponse.server_error(
            "Database error occurred. Please ensure migrations are run and database is properly configured."
        )

    response = exception_handler(exc, context)

    if response is not None:
        # Standard DRF exceptions (APIException subclasses) end up here too.
        detail = getattr(exc, "detail", None)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            return APIResponse.validation_error(
                "Invalid request",
                _normalize_errors(detail),
            )

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return APIResponse.unauthorized("Authentication required")

        if response.status_code == status.HTTP_403_FORBIDDEN:
            return APIResponse.forbidden("Permission denied")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            return APIResponse.not_found("Route not found")

        message = (
            _stringify_detail(detail)
            if detail is not None
            else "An error occurred"
        )
        error = _normalize_errors(detail)
        return APIResponse.error(
            message=message,
            error=error,
            status_code=response.status_code,
        )

    # Non-DRF exceptions: never allow Django's default HTML error page to leak.
    if isinstance(exc, APIException):
        return APIResponse.error(
            message=_stringify_detail(getattr(exc, "detail", "An error occurred")),
            error=_normalize_errors(getattr(exc, "detail", None)),
            status_code=getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR),
        )

    return APIResponse.server_error("Internal server error")


def custom_404_handler(request, exception):
    return JsonResponse(
        {
            "success": False,
            "data": {},
            "error": {},
            "message": "Route not found",
        },
        status=404,
    )


def custom_500_handler(request):
    return JsonResponse(
        {
            "success": False,
            "data": {},
            "error": {},
            "message": "Internal server error",
        },
        status=500,
    )
