from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.exceptions import Conflict
from .models import Ticket, TicketHistory

TRANSITIONS = {
    Ticket.Status.OPEN: {Ticket.Status.IN_PROGRESS, Ticket.Status.CANCELED},
    Ticket.Status.IN_PROGRESS: {Ticket.Status.WAITING, Ticket.Status.RESOLVED},
    Ticket.Status.WAITING: {Ticket.Status.IN_PROGRESS},
    Ticket.Status.RESOLVED: {Ticket.Status.IN_PROGRESS, Ticket.Status.CLOSED},
    Ticket.Status.CLOSED: set(),
    Ticket.Status.CANCELED: set(),
}


def is_technician(user):
    return user.is_superuser or user.role in ("TECNICO", "ADMIN")


@transaction.atomic
def transition(ticket, new_status, user, solution=""):
    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
    previous = ticket.status
    if new_status not in TRANSITIONS.get(previous, set()):
        raise Conflict({"status": "Transição de status inválida."})

    requester = user.id == ticket.requester_id
    requester_transition = requester and (
        (previous == Ticket.Status.OPEN and new_status == Ticket.Status.CANCELED)
        or (previous == Ticket.Status.RESOLVED and new_status == Ticket.Status.IN_PROGRESS)
        or (previous == Ticket.Status.WAITING and new_status == Ticket.Status.IN_PROGRESS)
    )
    technician_transition = is_technician(user) and (
        (previous == Ticket.Status.OPEN and new_status in (Ticket.Status.IN_PROGRESS, Ticket.Status.CANCELED))
        or (previous == Ticket.Status.IN_PROGRESS and new_status in (Ticket.Status.WAITING, Ticket.Status.RESOLVED))
        or (previous == Ticket.Status.WAITING and new_status == Ticket.Status.IN_PROGRESS)
        or (previous == Ticket.Status.RESOLVED and new_status in (Ticket.Status.IN_PROGRESS, Ticket.Status.CLOSED))
    )
    if not (requester_transition or technician_transition):
        raise Conflict({"status": "Seu perfil não pode realizar esta transição de status."})

    if new_status == Ticket.Status.RESOLVED:
        if not solution.strip():
            raise ValidationError({"solution": "A solução é obrigatória para resolver o chamado."})
        ticket.solution = solution.strip()
        ticket.resolved_at = timezone.now()
    elif previous == Ticket.Status.RESOLVED and new_status == Ticket.Status.IN_PROGRESS:
        ticket.resolved_at = None

    ticket.status = new_status
    ticket.save()
    TicketHistory.objects.create(ticket=ticket, previous_status=previous, new_status=new_status, changed_by=user)
    return ticket
