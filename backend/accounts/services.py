"""Controle de tentativas de login e bloqueio temporário por IP.

Regra: após `LOGIN_MAX_ATTEMPTS` falhas consecutivas (padrão 5), o IP é
bloqueado por `LOGIN_BLOCK_MINUTES` minutos (padrão 20).

O estado fica no banco (não em memória) para permanecer consistente entre os
múltiplos workers do Gunicorn e sobreviver a reinícios. O IP nunca é gravado em
texto claro: usamos o mesmo hash com salt aplicado na auditoria.
"""

import hashlib
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from audit.services import client_ip

from .models import LoginAttempt


def ip_fingerprint(request):
    raw_ip = client_ip(request)
    if not raw_ip:
        return ""
    return hashlib.sha256(f"{settings.AUDIT_IP_SALT}:{raw_ip}".encode()).hexdigest()


def max_attempts():
    return max(1, int(getattr(settings, "LOGIN_MAX_ATTEMPTS", 5)))


def block_duration():
    return timedelta(minutes=max(1, int(getattr(settings, "LOGIN_BLOCK_MINUTES", 20))))


def check_block(request):
    """Retorna os segundos restantes de bloqueio para o IP, ou 0 se liberado."""
    fingerprint = ip_fingerprint(request)
    if not fingerprint:
        return 0
    attempt = LoginAttempt.objects.filter(ip_hash=fingerprint).first()
    if not attempt:
        return 0
    now = timezone.now()
    remaining = attempt.seconds_remaining(now)
    if remaining:
        return remaining
    if attempt.blocked_until and attempt.blocked_until <= now:
        # Bloqueio expirado: zera o contador para reiniciar o ciclo de tentativas.
        LoginAttempt.objects.filter(pk=attempt.pk).update(failures=0, blocked_until=None)
    return 0


@transaction.atomic
def register_failure(request):
    """Contabiliza uma falha e bloqueia o IP ao atingir o limite.

    Retorna (tentativas_restantes, segundos_de_bloqueio).
    """
    fingerprint = ip_fingerprint(request)
    if not fingerprint:
        return max_attempts(), 0

    attempt, _ = LoginAttempt.objects.get_or_create(ip_hash=fingerprint)
    attempt = LoginAttempt.objects.select_for_update().get(pk=attempt.pk)

    now = timezone.now()
    if attempt.blocked_until and attempt.blocked_until > now:
        return 0, attempt.seconds_remaining(now)
    if attempt.blocked_until and attempt.blocked_until <= now:
        attempt.failures = 0
        attempt.blocked_until = None

    attempt.failures += 1
    attempt.last_failure_at = now
    limit = max_attempts()
    if attempt.failures >= limit:
        attempt.blocked_until = now + block_duration()
        attempt.save(update_fields=["failures", "last_failure_at", "blocked_until", "updated_at"])
        return 0, attempt.seconds_remaining(now)

    attempt.save(update_fields=["failures", "last_failure_at", "blocked_until", "updated_at"])
    return limit - attempt.failures, 0


def register_success(request):
    """Limpa o histórico de falhas do IP após autenticação bem-sucedida."""
    fingerprint = ip_fingerprint(request)
    if fingerprint:
        LoginAttempt.objects.filter(ip_hash=fingerprint).update(failures=0, blocked_until=None)
