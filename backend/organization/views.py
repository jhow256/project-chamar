from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from audit.services import audit
from core.permissions import IsTechnician
from .models import EquipmentType, Sector
from .serializers import EquipmentTypeSerializer, SectorSerializer


class CatalogViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    audit_resource = "catalog"
    audit_prefix = "CATALOG"

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsTechnician()]

    def perform_create(self, serializer):
        instance = serializer.save()
        audit(self.request, f"{self.audit_prefix}_CREATED", f"{self.audit_resource}:{instance.pk}")

    def perform_update(self, serializer):
        instance = serializer.save()
        audit(
            self.request,
            f"{self.audit_prefix}_UPDATED",
            f"{self.audit_resource}:{instance.pk}",
            {"campos": sorted(serializer.validated_data)},
        )


class SectorViewSet(CatalogViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    audit_resource = "sector"
    audit_prefix = "SECTOR"


class EquipmentTypeViewSet(CatalogViewSet):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    audit_resource = "equipment-type"
    audit_prefix = "EQUIPMENT_TYPE"
