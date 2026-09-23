import django_filters
from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    data_inicio = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    data_fim = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Ticket
        fields = {"status": ["exact"], "urgency_perceived": ["exact"], "priority": ["exact"], "category": ["exact"], "equipment_type": ["exact"], "sector": ["exact"], "technician": ["exact"]}
