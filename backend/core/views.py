from django.db import connection
from django.db.utils import DatabaseError
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return Response({"status": "indisponivel", "banco": "indisponivel"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({"status": "ok", "banco": "ok"})
