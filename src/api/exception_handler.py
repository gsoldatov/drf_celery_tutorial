from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    # Handle DB network errors
    if isinstance(exc, OperationalError):
        return Response(
            {"detail": "Service temporarily unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    # Default
    return drf_exception_handler(exc, context)
