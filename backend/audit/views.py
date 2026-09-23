from rest_framework import viewsets
from core.permissions import IsAdmin
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["action", "user"]
    search_fields = ["resource"]
