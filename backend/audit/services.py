import hashlib
from django.conf import settings
from .models import AuditLog


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if settings.TRUST_X_FORWARDED_FOR and forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def audit(request, action, resource, details=None):
    raw_ip = client_ip(request)
    ip_hash = hashlib.sha256(f"{settings.AUDIT_IP_SALT}:{raw_ip}".encode()).hexdigest() if raw_ip else ""
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    return AuditLog.objects.create(user=user, action=action, resource=resource, ip_hash=ip_hash, details=details or {})
