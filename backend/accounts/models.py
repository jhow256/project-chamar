import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        if not extra["is_staff"] or not extra["is_superuser"]:
            raise ValueError("O superusuário deve ter is_staff e is_superuser ativos.")
        if extra["role"] != User.Role.ADMIN:
            raise ValueError("O superusuário deve possuir o perfil ADMIN.")
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    class Role(models.TextChoices):
        COLLABORATOR = "COLABORADOR", "Colaborador"
        TECHNICIAN = "TECNICO", "Técnico"
        ADMIN = "ADMIN", "Administrador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField("e-mail", unique=True)
    name = models.CharField("nome", max_length=150)
    role = models.CharField("perfil", max_length=12, choices=Role.choices, default=Role.COLLABORATOR)
    sector = models.ForeignKey("organization.Sector", on_delete=models.PROTECT, null=True, blank=True, related_name="users")
    anonymized_at = models.DateTimeField("anonimizado em", null=True, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(role__in=["COLABORADOR", "TECNICO", "ADMIN"]), name="accounts_user_valid_role"),
        ]

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        self.is_staff = self.role == self.Role.ADMIN
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"role", "is_staff"}
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Consent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="consents")
    policy_version = models.CharField("versão da política", max_length=30)
    accepted_at = models.DateTimeField("aceito em", auto_now_add=True)

    class Meta:
        ordering = ["-accepted_at"]


class LoginAttempt(models.Model):
    """Controle de tentativas de login e bloqueio temporário por IP.

    O IP é armazenado apenas como hash com salt (pseudonimização/LGPD).
    """

    ip_hash = models.CharField("hash do IP", max_length=64, unique=True)
    failures = models.PositiveIntegerField("falhas consecutivas", default=0)
    last_failure_at = models.DateTimeField("última falha em", null=True, blank=True)
    blocked_until = models.DateTimeField("bloqueado até", null=True, blank=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "tentativa de login"
        verbose_name_plural = "tentativas de login"
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["blocked_until"])]

    def __str__(self):
        return f"{self.ip_hash[:12]}… ({self.failures} falha(s))"

    def seconds_remaining(self, now):
        if not self.blocked_until or self.blocked_until <= now:
            return 0
        return int((self.blocked_until - now).total_seconds())
