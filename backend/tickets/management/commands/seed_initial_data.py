import os

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from organization.models import EquipmentType, Sector
from tickets.models import Category

INITIAL_PASSWORD = os.environ.get("INITIAL_USER_PASSWORD", "Dev@Chamar2026!")
SECTORS = [
    "ARQUIVO", "ASCOOM", "ASTEC", "CHGAB", "CI", "CMDU", "CONTROLADORIA",
    "CTPCU", "DIAF", "DIAP", "DICON", "DIOP", "DIPA", "DIPU", "DIRAF",
    "DOM", "DPLA", "GAPIS", "GCA", "GEAT", "GEN", "GEP", "GFAP", "GFO",
    "GFP", "GGP", "GIG", "GINF", "GIT", "GLT", "GMU", "GPH", "GPLAN",
    "GPMS", "GPS", "OUVIDORIA", "PRESID", "PROJUR", "VPRES", "OUTROS",
    "REPROGRAFIA",
]
EQUIPMENT_TYPES = [
    "COMPUTADOR", "IMPRESSORA", "MONITOR", "NOBREAK", "NOTEBOOK",
    "PONTO ELETRÔNICO", "PROJETOR", "ROTEADOR", "SCANNER", "SERVIDOR",
    "SWITCH", "NENHUM", "RÉGUA", "TELEFONE", "SISTEMAS", "EMAIL",
]
CATEGORIES = [
    "Hardware", "Software", "Rede e Internet", "Acesso e Senhas", "Sistemas",
    "E-mail", "Telefonia", "Outros",
]
TECHNICIANS = [
    ("Rafael Santos", "rafael.santos@chamar.local"),
    ("Mateus Maciel", "mateus.maciel@chamar.local"),
    ("Nayane Reis", "nayane.reis@chamar.local"),
    ("Ronaldo Silva", "ronaldo.silva@chamar.local"),
    ("Sabatta Macedo", "sabatta.macedo@chamar.local"),
    ("Sebastião Barbosa", "sebastiao.barbosa@chamar.local"),
    ("Edeson Vasconcelos", "edeson.vasconcelos@chamar.local"),
    ("Kelven Abraão", "kelven.abraao@chamar.local"),
    ("Rodrigo Sousa", "rodrigo.sousa@chamar.local"),
]


class Command(BaseCommand):
    help = "Cria ou reativa os catálogos e técnicos iniciais, sem dados demonstrativos."

    @transaction.atomic
    def handle(self, *args, **options):
        sectors = {name: self.upsert_catalog(Sector, name) for name in SECTORS}
        for name in EQUIPMENT_TYPES:
            self.upsert_catalog(EquipmentType, name)
        for name in CATEGORIES:
            self.upsert_catalog(Category, name)

        admin_email = os.environ.get("INITIAL_ADMIN_EMAIL", "admin@chamar.local").strip().lower()
        admin, admin_created = User.objects.get_or_create(
            email=admin_email,
            defaults={"name": "Administrador", "role": User.Role.ADMIN, "sector": sectors["OUTROS"], "is_active": True},
        )
        if admin_created:
            admin.set_password(INITIAL_PASSWORD)
            admin.save(update_fields=["password"])

        collaborator_email = os.environ.get("INITIAL_COLLABORATOR_EMAIL", "colaborador@chamar.local").strip().lower()
        collaborator, collaborator_created = User.objects.get_or_create(
            email=collaborator_email,
            defaults={"name": "Colaborador Demonstração", "role": User.Role.COLLABORATOR, "sector": sectors["OUTROS"], "is_active": True},
        )
        if collaborator_created:
            collaborator.set_password(INITIAL_PASSWORD)
            collaborator.save(update_fields=["password"])

        created_users = 0
        for name, email in TECHNICIANS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": name, "role": User.Role.TECHNICIAN, "sector": sectors["OUTROS"], "is_active": True},
            )
            if created:
                user.set_password(INITIAL_PASSWORD)
                user.save(update_fields=["password"])
                created_users += 1
            else:
                changed = []
                for field, value in (("name", name), ("role", User.Role.TECHNICIAN), ("sector", sectors["OUTROS"]), ("is_active", True), ("is_staff", False)):
                    if getattr(user, field) != value:
                        setattr(user, field, value)
                        changed.append(field)
                if changed:
                    user.save(update_fields=changed)

        self.stdout.write(self.style.SUCCESS(f"Dados iniciais prontos; {created_users} técnico(s) criado(s)."))
        self.stdout.write(f"Administrador inicial: {admin_email} ({'criado' if admin_created else 'já existente'})")
        self.stdout.write(f"Colaborador inicial: {collaborator_email} ({'criado' if collaborator_created else 'já existente'})")
        self.stdout.write("Técnicos: " + ", ".join(email for _, email in TECHNICIANS))

    @staticmethod
    def upsert_catalog(model, name):
        item, _ = model.objects.get_or_create(name=name, defaults={"active": True})
        if not item.active:
            item.active = True
            item.save(update_fields=["active"])
        return item
