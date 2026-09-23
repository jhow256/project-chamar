from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(read_only=True)
    class Meta:
        model = AuditLog
        fields = ["id", "user_id", "action", "resource", "ip_hash", "details", "created_at"]
