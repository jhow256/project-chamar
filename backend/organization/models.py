from django.db import models


class NamedActiveCatalog(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)
    active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sector(NamedActiveCatalog):
    class Meta(NamedActiveCatalog.Meta):
        verbose_name = "setor"
        verbose_name_plural = "setores"


class EquipmentType(NamedActiveCatalog):
    class Meta(NamedActiveCatalog.Meta):
        verbose_name = "tipo de equipamento"
        verbose_name_plural = "tipos de equipamento"
