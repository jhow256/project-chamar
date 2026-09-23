from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField("ação", max_length=80)
    resource = models.CharField("recurso", max_length=120)
    ip_hash = models.CharField("hash do IP", max_length=64, blank=True)
    details = models.JSONField("detalhes", default=dict, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("O log de auditoria é imutável.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("O log de auditoria é imutável.")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]
