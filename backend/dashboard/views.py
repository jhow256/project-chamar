import csv
from datetime import timedelta
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core.permissions import IsTechnician
from tickets.models import Ticket

DONE = [Ticket.Status.RESOLVED, Ticket.Status.CLOSED]


def range_from(request):
    end = timezone.now()
    period = request.query_params.get("periodo", "30d")
    days = int(period[:-1]) if period in {"7d", "30d", "90d"} else 30
    start = end - timedelta(days=days)
    try:
        if request.query_params.get("data_inicio"):
            start = timezone.datetime.fromisoformat(request.query_params["data_inicio"])
            if timezone.is_naive(start):
                start = timezone.make_aware(start)
        if request.query_params.get("data_fim"):
            end = timezone.datetime.fromisoformat(request.query_params["data_fim"])
            if timezone.is_naive(end):
                end = timezone.make_aware(end)
    except ValueError as exc:
        raise ValidationError({"periodo": "Informe datas válidas no padrão ISO 8601."}) from exc
    if start > end:
        raise ValidationError({"periodo": "A data inicial não pode ser posterior à data final."})
    return start, end


def base(request):
    start, end = range_from(request)
    return Ticket.objects.filter(deleted_at__isnull=True, created_at__range=(start, end))


def schema_object(view):
    return extend_schema(responses={200: OpenApiTypes.OBJECT})(view)


@schema_object
@api_view(["GET"])
@permission_classes([IsTechnician])
def summary(request):
    duration = ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField())
    stats = base(request).aggregate(total=Count("id"), opened=Count("id", filter=Q(status=Ticket.Status.OPEN)),
        in_progress=Count("id", filter=Q(status__in=[Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING])),
        closed=Count("id", filter=Q(status__in=DONE)), average_resolution=Avg(duration, filter=Q(resolved_at__isnull=False)), average_rating=Avg("rating"))
    average = stats.pop("average_resolution")
    stats["average_resolution_seconds"] = average.total_seconds() if average else None
    stats["resolution_rate"] = round(stats["closed"] * 100 / stats["total"], 2) if stats["total"] else 0
    return Response(stats)


def grouped(request, label):
    return Response(list(base(request).values(label).annotate(total=Count("id")).order_by("-total")[:10]))


@schema_object
@api_view(["GET"])
@permission_classes([IsTechnician])
def by_sector(request): return grouped(request, "sector__name")


@schema_object
@api_view(["GET"])
@permission_classes([IsTechnician])
def by_category(request): return grouped(request, "category__name")


@schema_object
@api_view(["GET"])
@permission_classes([IsTechnician])
def by_technician(request):
    start, end = range_from(request)
    rows = Ticket.objects.filter(
        deleted_at__isnull=True,
        resolved_at__range=(start, end),
        status__in=DONE,
        technician__isnull=False,
    ).values("technician__name").annotate(total=Count("id")).order_by("-total")
    return Response(list(rows))


@schema_object
@api_view(["GET"])
@permission_classes([IsTechnician])
def timeline(request):
    start, end = range_from(request)
    active = Ticket.objects.filter(deleted_at__isnull=True)
    opened = active.filter(created_at__range=(start, end)).annotate(day=TruncDate("created_at")).values("day").annotate(opened=Count("id")).order_by("day")
    resolved = active.filter(resolved_at__range=(start, end), status__in=DONE).annotate(day=TruncDate("resolved_at")).values("day").annotate(resolved=Count("id")).order_by("day")
    data = {}
    for row in opened: data.setdefault(row["day"].isoformat(), {"opened": 0, "resolved": 0})["opened"] = row["opened"]
    for row in resolved: data.setdefault(row["day"].isoformat(), {"opened": 0, "resolved": 0})["resolved"] = row["resolved"]
    return Response([{"date": day, **values} for day, values in sorted(data.items())])


@extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
@api_view(["GET"])
@permission_classes([IsTechnician])
def export_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="dashboard.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Número", "Título", "Status", "Urgência percebida", "Prioridade final", "Setor", "Categoria", "Tipo de equipamento", "Técnico", "Criado em", "Resolvido em"])
    for t in base(request).select_related("sector", "category", "equipment_type", "technician"):
        writer.writerow([t.number, t.title, t.status, t.urgency_perceived, t.priority, t.sector.name, t.category.name, t.equipment_type.name if t.equipment_type else "", t.technician.name if t.technician else "", t.created_at.isoformat(), t.resolved_at.isoformat() if t.resolved_at else ""])
    return response
