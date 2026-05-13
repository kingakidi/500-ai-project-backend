from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    @staticmethod
    def _envelope(
        *,
        success: bool,
        message: str,
        data,
        error,
        status_code: int,
    ):
        return Response(
            {
                "success": success,
                "data": data,
                "error": error,
                "message": message,
            },
            status=status_code,
        )

    @staticmethod
    def success(message="Success", data=None, status_code=status.HTTP_200_OK):
        if data is None:
            data = {}
        return APIResponse._envelope(
            success=True,
            message=message,
            data=data,
            error={},
            status_code=status_code,
        )

    @staticmethod
    def error(message="Error", error=None, status_code=status.HTTP_400_BAD_REQUEST):
        if error is None:
            error = {}
        return APIResponse._envelope(
            success=False,
            message=message,
            data={},
            error=error,
            status_code=status_code,
        )

    @staticmethod
    def not_found(message="Resource not found", error=None):
        return APIResponse.error(
            message=message,
            error=error,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def duplicate(message="Resource already exists", error=None):
        return APIResponse.error(
            message=message,
            error=error,
            status_code=status.HTTP_409_CONFLICT,
        )

    @staticmethod
    def bad_request(message="Invalid request", error=None):
        return APIResponse.error(
            message=message,
            error=error,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def unauthorized(message="Unauthorized", error=None):
        return APIResponse.error(
            message=message,
            error=error,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def forbidden(message="Forbidden", error=None):
        return APIResponse.error(
            message=message,
            error=error,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    @staticmethod
    def validation_error(message="Validation error", errors=None):
        return APIResponse.bad_request(
            message=message,
            error=errors if errors is not None else {},
        )

    @staticmethod
    def server_error(message="Internal server error", error=None):
        return APIResponse.error(
            message=message,
            error=error,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @staticmethod
    def created(message="Resource created successfully", data=None):
        return APIResponse.success(
            message=message, data=data, status_code=status.HTTP_201_CREATED
        )

    @staticmethod
    def no_content(message="Deleted", data=None):
        if data is None:
            data = {}
        return APIResponse._envelope(
            success=True,
            message=message,
            data=data,
            error={},
            status_code=status.HTTP_204_NO_CONTENT,
        )
