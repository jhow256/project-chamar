from rest_framework import serializers

from .models import EquipmentType, Sector


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "name", "active", "created_at"]
        read_only_fields = ["id", "created_at"]


class SectorSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = Sector


class EquipmentTypeSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = EquipmentType
