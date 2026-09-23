from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from tickets.models import Ticket, TicketHistory


class Command(BaseCommand):
    help = "Fecha chamados resolvidos sem interação recente (padrão: 5 dias)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=5,
            help="Quantidade de dias corridos sem interação antes do fechamento.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError("O prazo deve ser de pelo menos 1 dia.")

        cutoff = timezone.now() - timedelta(days=days)
        tickets = (
            Ticket.objects.select_for_update()
            .filter(
                status=Ticket.Status.RESOLVED,
                deleted_at__isnull=True,
                resolved_at__lte=cutoff,
            )
            .exclude(comments__created_at__gt=cutoff)
            .select_related("technician", "requester")
            .distinct()
        )

        closed = 0
        for ticket in tickets:
            actor = ticket.technician or ticket.requester
            previous = ticket.status
            ticket.status = Ticket.Status.CLOSED
            ticket.save(update_fields=["status", "updated_at"])
            TicketHistory.objects.create(
                ticket=ticket,
                previous_status=previous,
                new_status=Ticket.Status.CLOSED,
                changed_by=actor,
                details={"automatico": True, "dias_sem_interacao": days},
            )
            closed += 1

        self.stdout.write(
            self.style.SUCCESS(f"Fechamento automático concluído: {closed} chamado(s).")
        )
