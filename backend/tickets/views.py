from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.services import audit
from core.exceptions import Conflict
from core.permissions import IsTechnician
from .filters import TicketFilter
from .models import Attachment, Category, Comment, Ticket, TicketHistory
from .serializers import AttachmentSerializer, CategorySerializer, CommentSerializer, HistorySerializer, TicketSerializer
from .services import is_technician, transition


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ("list", "retrieve") else [IsTechnician()]

    def perform_create(self, serializer):
        category = serializer.save()
        audit(self.request, "CATEGORY_CREATED", f"category:{category.pk}")

    def perform_update(self, serializer):
        category = serializer.save()
        audit(self.request, "CATEGORY_UPDATED", f"category:{category.pk}", {"campos": sorted(serializer.validated_data)})


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    filterset_class = TicketFilter
    search_fields = ["number", "title", "description"]
    ordering_fields = ["created_at", "updated_at", "urgency_perceived", "priority", "status"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = Ticket.objects.select_related("requester", "technician", "sector", "category", "equipment_type")
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        user = self.request.user
        privileged = is_technician(user)
        if self.action in ("delete", "restore"):
            return qs if privileged else qs.filter(requester=user)
        qs = qs.filter(deleted_at__isnull=True)
        return qs if privileged else qs.filter(requester=user)

    @transaction.atomic
    def perform_create(self, serializer):
        if not self.request.user.sector_id:
            raise ValidationError({"sector": "Seu usuário precisa estar vinculado a um setor."})
        ticket = serializer.save(requester=self.request.user, sector=self.request.user.sector)
        TicketHistory.objects.create(ticket=ticket, previous_status="", new_status=Ticket.Status.OPEN, changed_by=self.request.user, details={"urgencia_percebida": ticket.urgency_perceived, "prioridade_final": ticket.priority})
        audit(self.request, "TICKET_CREATED", f"ticket:{ticket.pk}")

    @transaction.atomic
    def perform_update(self, serializer):
        user = self.request.user
        privileged = is_technician(user)
        if not privileged and serializer.instance.status != Ticket.Status.OPEN:
            raise Conflict({"status": "O colaborador só pode editar chamados abertos."})
        allowed = {"title", "description", "urgency_perceived", "category", "equipment_type"}
        if privileged:
            allowed.add("priority")
        forbidden = set(serializer.validated_data) - allowed
        if forbidden:
            raise PermissionDenied("Há campos que seu perfil não pode alterar.")
        tracked = ("urgency_perceived", "priority", "category_id", "equipment_type_id")
        before = {field: getattr(serializer.instance, field) for field in tracked}
        ticket = serializer.save()
        changed = {}
        labels = {"urgency_perceived": "urgencia_percebida", "priority": "prioridade", "category_id": "categoria", "equipment_type_id": "tipo_equipamento"}
        for field in tracked:
            current = getattr(ticket, field)
            if before[field] != current:
                changed[labels[field]] = {"anterior": before[field], "novo": current}
        if changed:
            TicketHistory.objects.create(ticket=ticket, previous_status=ticket.status, new_status=ticket.status, changed_by=user, details={"campos_alterados": changed})
        audit(self.request, "TICKET_UPDATED", f"ticket:{ticket.pk}", {"campos": sorted(serializer.validated_data)})

    @action(detail=True, methods=["post"], permission_classes=[IsTechnician])
    @transaction.atomic
    def assign(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status in (Ticket.Status.RESOLVED, Ticket.Status.CLOSED, Ticket.Status.CANCELED):
            raise Conflict({"status": "Não é possível atribuir um chamado finalizado."})
        previous_id = ticket.technician_id
        ticket.technician = request.user
        ticket.save(update_fields=["technician", "updated_at"])
        TicketHistory.objects.create(ticket=ticket, previous_status=ticket.status, new_status=ticket.status, changed_by=request.user, details={"atribuicao": {"anterior": str(previous_id) if previous_id else None, "novo": str(request.user.id)}})
        if ticket.status == Ticket.Status.OPEN:
            ticket = transition(ticket, Ticket.Status.IN_PROGRESS, request.user)
        audit(request, "TICKET_ASSIGNED", f"ticket:{ticket.pk}")
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        ticket = transition(self.get_object(), request.data.get("status"), request.user, request.data.get("solution", ""))
        audit(request, "TICKET_STATUS_CHANGED", f"ticket:{ticket.pk}", {"status": ticket.status})
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTechnician])
    def resolve(self, request, pk=None):
        ticket = transition(self.get_object(), Ticket.Status.RESOLVED, request.user, request.data.get("solution", ""))
        audit(request, "TICKET_RESOLVED", f"ticket:{ticket.pk}")
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        ticket = transition(self.get_object(), Ticket.Status.CANCELED, request.user)
        audit(request, "TICKET_CANCELED", f"ticket:{ticket.pk}")
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status != Ticket.Status.RESOLVED:
            raise Conflict({"status": "Somente chamados resolvidos podem ser reabertos."})
        ticket = transition(ticket, Ticket.Status.IN_PROGRESS, request.user)
        audit(request, "TICKET_REOPENED", f"ticket:{ticket.pk}", {"status": Ticket.Status.IN_PROGRESS})
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def delete(self, request, pk=None):
        ticket = Ticket.objects.select_for_update().get(pk=self.get_object().pk)
        if not is_technician(request.user):
            raise PermissionDenied("Somente técnicos e administradores podem excluir chamados.")
        if ticket.deleted_at:
            raise Conflict({"deleted_at": "O chamado já está excluído."})
        ticket.deleted_at = timezone.now()
        ticket.save(update_fields=["deleted_at", "updated_at"])
        TicketHistory.objects.create(ticket=ticket, previous_status=ticket.status, new_status=ticket.status, changed_by=request.user, details={"exclusao_logica": True})
        audit(request, "TICKET_DELETED", f"ticket:{ticket.pk}")
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def restore(self, request, pk=None):
        ticket = Ticket.objects.select_for_update().get(pk=self.get_object().pk)
        if not is_technician(request.user):
            raise PermissionDenied("Somente técnicos e administradores podem restaurar chamados.")
        if not ticket.deleted_at:
            raise Conflict({"deleted_at": "O chamado não está excluído."})
        ticket.deleted_at = None
        ticket.save(update_fields=["deleted_at", "updated_at"])
        TicketHistory.objects.create(ticket=ticket, previous_status=ticket.status, new_status=ticket.status, changed_by=request.user, details={"restauracao": True})
        audit(request, "TICKET_RESTORED", f"ticket:{ticket.pk}")
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def rate(self, request, pk=None):
        ticket = Ticket.objects.select_for_update().get(pk=self.get_object().pk)
        if ticket.requester_id != request.user.id or ticket.status not in (Ticket.Status.RESOLVED, Ticket.Status.CLOSED):
            raise PermissionDenied("Somente o solicitante pode avaliar um chamado resolvido ou fechado.")
        if ticket.rating is not None:
            raise Conflict({"rating": "Este chamado já foi avaliado e a avaliação não pode ser alterada."})
        try:
            rating = int(request.data.get("rating"))
        except (TypeError, ValueError):
            rating = 0
        if rating not in range(1, 6):
            raise ValidationError({"rating": "A avaliação deve ser de 1 a 5."})
        ticket.rating = rating
        ticket.save(update_fields=["rating", "updated_at"])
        TicketHistory.objects.create(ticket=ticket, previous_status=ticket.status, new_status=ticket.status, changed_by=request.user, details={"avaliacao": rating})
        audit(request, "TICKET_RATED", f"ticket:{ticket.pk}", {"rating": rating})
        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        ticket = self.get_object()
        if request.method == "GET":
            return Response(CommentSerializer(ticket.comments.select_related("author"), many=True).data)
        if ticket.status in (Ticket.Status.CLOSED, Ticket.Status.CANCELED):
            raise Conflict({"status": "Não é possível adicionar comentários a um chamado fechado ou cancelado."})
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, author=request.user)
        if ticket.status == Ticket.Status.WAITING and ticket.requester_id == request.user.id:
            transition(ticket, Ticket.Status.IN_PROGRESS, request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def attachments(self, request, pk=None):
        ticket = self.get_object()
        if request.method == "GET":
            return Response(AttachmentSerializer(ticket.attachments.all(), many=True, context={"request": request}).data)
        if ticket.status in (Ticket.Status.CLOSED, Ticket.Status.CANCELED):
            raise Conflict({"status": "Não é possível adicionar anexos a um chamado fechado ou cancelado."})
        serializer = AttachmentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]
        detected_mime = serializer.validated_data["detected_mime_type"]
        attachment = serializer.save(ticket=ticket, uploader=request.user, original_name=file.name, mime_type=detected_mime, size_bytes=file.size)
        TicketHistory.objects.create(ticket=ticket, previous_status=ticket.status, new_status=ticket.status, changed_by=request.user, details={"anexo": {"id": attachment.pk, "mime": detected_mime}})
        audit(request, "ATTACHMENT_UPLOADED", f"attachment:{attachment.pk}")
        return Response(AttachmentSerializer(attachment, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        history = self.get_object().history.select_related("changed_by")
        return Response(HistorySerializer(history, many=True).data)


@extend_schema(responses={(200, "application/octet-stream"): OpenApiTypes.BINARY})
@api_view(["GET"])
def download_attachment(request, pk):
    visible = Ticket.objects.filter(deleted_at__isnull=True)
    if not is_technician(request.user):
        visible = visible.filter(requester=request.user)
    attachment = get_object_or_404(Attachment.objects.filter(ticket__in=visible), pk=pk)
    try:
        return FileResponse(attachment.file.open("rb"), as_attachment=True, filename=attachment.original_name, content_type=attachment.mime_type)
    except FileNotFoundError as exc:
        raise Http404 from exc
