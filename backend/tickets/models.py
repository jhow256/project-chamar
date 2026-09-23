import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


def attachment_path(instance, filename):
    return f"attachments/{instance.ticket_id}/{uuid.uuid4()}{Path(filename).suffix.lower()}"


class Category(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)
    active = models.BooleanField("ativa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "ABERTO", "Aberto"
        IN_PROGRESS = "EM_ATENDIMENTO", "Em atendimento"
        WAITING = "AGUARDANDO_USUARIO", "Aguardando usuário"
        RESOLVED = "RESOLVIDO", "Resolvido"
        CLOSED = "FECHADO", "Fechado"
        CANCELED = "CANCELADO", "Cancelado"

    class Priority(models.TextChoices):
        LOW = "BAIXA", "Baixa"
        MEDIUM = "MEDIA", "Média"
        HIGH = "ALTA", "Alta"
        CRITICAL = "CRITICA", "Crítica"

    number = models.CharField("número", max_length=20, unique=True, null=True, blank=True)
    title = models.CharField("título", max_length=180)
    description = models.TextField("descrição")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    urgency_perceived = models.CharField("urgência percebida", max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    priority = models.CharField("prioridade final", max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_tickets")
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="assigned_tickets")
    sector = models.ForeignKey("organization.Sector", on_delete=models.PROTECT, related_name="tickets")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="tickets")
    equipment_type = models.ForeignKey("organization.EquipmentType", on_delete=models.PROTECT, null=True, blank=True, related_name="tickets")
    solution = models.TextField("solução", blank=True)
    rating = models.PositiveSmallIntegerField("avaliação", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["sector", "created_at"]), models.Index(fields=["technician", "resolved_at"]), models.Index(fields=["created_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(status__in=["ABERTO", "EM_ATENDIMENTO", "AGUARDANDO_USUARIO", "RESOLVIDO", "FECHADO", "CANCELADO"]), name="tickets_ticket_valid_status"),
            models.CheckConstraint(condition=models.Q(urgency_perceived__in=["BAIXA", "MEDIA", "ALTA", "CRITICA"]), name="tickets_ticket_valid_urgency"),
            models.CheckConstraint(condition=models.Q(priority__in=["BAIXA", "MEDIA", "ALTA", "CRITICA"]), name="tickets_ticket_valid_priority"),
            models.CheckConstraint(condition=models.Q(rating__isnull=True) | models.Q(rating__range=(1, 5)), name="tickets_ticket_valid_rating"),
            models.CheckConstraint(condition=~models.Q(status__in=["RESOLVIDO", "FECHADO"]) | models.Q(resolved_at__isnull=False), name="tickets_ticket_resolved_has_date"),
        ]

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.number:
            self.number = f"CH-{self.created_at.year}-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(number=self.number)

    def delete(self, *args, **kwargs):
        raise ValueError("Chamados não podem ser excluídos fisicamente.")


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="comments")
    text = models.TextField("texto")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="attachments")
    file = models.FileField(upload_to=attachment_path, validators=[FileExtensionValidator(["png", "jpg", "jpeg", "pdf"])])
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    original_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="history")
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_changes")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("O histórico é imutável.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("O histórico é imutável.")
